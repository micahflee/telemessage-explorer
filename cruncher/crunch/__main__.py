import os
import re
import json

import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

import click

from .db import connect_db, create_tables, close_db
from .tm_objects import TMObjects
import base64


def extract_complete_json_objects(text):
    """
    Extracts complete JSON objects from a string
    """
    objects = []
    brace_level = 0
    start_idx = None

    for idx, char in enumerate(text):
        if char == "{":
            if brace_level == 0:
                start_idx = idx
            brace_level += 1
        elif char == "}":
            brace_level -= 1
            if brace_level == 0 and start_idx is not None:
                candidate = text[start_idx : idx + 1]
                try:
                    obj = json.loads(candidate)
                    objects.append(obj)
                except Exception:
                    pass  # Not valid JSON, skip
                start_idx = None
    return objects


def extract_crypto_objects(lines):
    """
    Extracts complete and non-empty cryptography objects like private keys,
    public keys, and certificates.
    """

    begin_markers = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN PUBLIC KEY-----",
        "-----BEGIN CERTIFICATE-----",
    ]
    end_markers = {
        "-----BEGIN PRIVATE KEY-----": "-----END PRIVATE KEY-----",
        "-----BEGIN PUBLIC KEY-----": "-----END PUBLIC KEY-----",
        "-----BEGIN CERTIFICATE-----": "-----END CERTIFICATE-----",
    }

    crypto_objects = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find the start of a crypto object
        for begin in begin_markers:
            idx = line.find(begin)
            if idx != -1:
                # Make sure the line starts with the marker (ignoring leading whitespace)
                start_pos = line.index(begin)
                candidate_lines = []
                # Only accept if nothing but whitespace before the marker
                if line[:start_pos].strip() == "":
                    candidate_lines.append(line[start_pos:].rstrip("\n"))
                    end_marker = end_markers[begin]
                    i += 1
                    valid = True
                    base64_lines = []
                    # Collect base64 lines until end marker
                    while i < len(lines):
                        l = lines[i].rstrip("\n")
                        if l == end_marker:
                            candidate_lines.append(l)
                            break
                        # Check if line is valid base64 (ignore empty lines)
                        if l.strip() == "":
                            candidate_lines.append(l)
                            i += 1
                            continue
                        try:
                            # Remove whitespace for base64 check
                            base64.b64decode(l.strip(), validate=True)
                            base64_lines.append(l)
                        except Exception:
                            valid = False
                            break
                        candidate_lines.append(l)
                        i += 1
                    else:
                        valid = False  # Did not find end marker
                    # Only add if valid, has end marker, and has at least one non-empty base64 line
                    if (
                        valid
                        and candidate_lines[-1] == end_marker
                        and len(base64_lines) > 0
                    ):
                        crypto_objects.append("\n".join(candidate_lines))
                break
        i += 1
    return crypto_objects


def import_objects(path, num_threads=0, num_skip=0):
    """
    Using threads, import objects from heap dumps into the database
    """
    if num_threads == 0:
        num_threads = os.cpu_count() or 4

    print(f"using {num_threads} threads")

    def extract_number(filename):
        return int(re.search(r"\d+", filename).group())

    data_files = [
        f
        for f in os.listdir(path)
        if f.endswith(".strings")
        and f.replace(".strings", "")
        not in [f"heapdump.{i}" for i in range(0, num_skip)]
    ]
    sorted_filenames = sorted(data_files, key=extract_number)
    total_files = len(sorted_filenames) + num_skip
    file_queue = Queue()
    for filename in sorted_filenames:
        file_queue.put(filename)

    progress_lock = threading.Lock()
    progress = {"current_file": num_skip}

    stop_event = threading.Event()

    def worker():
        conn = connect_db()
        while not file_queue.empty() and not stop_event.is_set():
            try:
                filename = file_queue.get_nowait()
            except Exception:
                break

            filename_without_string = filename.replace(".strings", "")

            try:
                with open(os.path.join(path, filename), "r") as f:
                    lines = f.readlines()

                # Detect JSON objects
                objects = []
                for line in lines:
                    objects.extend(extract_complete_json_objects(line))

                objs: TMObjects = TMObjects(filename_without_string)
                for obj in objects:
                    objs.analyze_object(obj)
                objs.display()
                objs.insert_objects(conn, filename_without_string)

                # Detect private keys, public keys, and certificates
                crypto_objects = extract_crypto_objects(lines)
                print(
                    f"[{filename_without_string}] found {len(crypto_objects):,} crypto objects"
                )
                objs.insert_crypto_objects(conn, crypto_objects)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

            with progress_lock:
                progress["current_file"] += 1
                print(
                    f"processed {progress['current_file']:,} of {total_files:,} files, {progress['current_file'] / total_files:.2%} complete"
                )
            file_queue.task_done()
        close_db(conn)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]
        try:
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            print("\nCtrl+C detected, shutting down...")
            stop_event.set()
            # Optionally, clear the queue so threads exit faster
            while not file_queue.empty():
                try:
                    file_queue.get_nowait()
                except Exception:
                    break
            executor.shutdown(wait=False)
            raise


@click.command()
@click.option(
    "--path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to folder with heap dump .strings files",
)
@click.option("--num-threads", default=0, help="Number of threads to run")
@click.option("--num-skip", default=0, help="Skip the first N heap dumps")
def main(path, num_threads, num_skip):
    conn = connect_db()
    create_tables(conn)
    close_db(conn)

    try:
        import_objects(path, num_threads, num_skip)
    except KeyboardInterrupt:
        print("Ctrl-C pressed, exiting...")


if __name__ == "__main__":
    main()

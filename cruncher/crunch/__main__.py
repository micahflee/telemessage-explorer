import os
import re
import json

import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

import click

from .db import connect_db, create_tables, close_db
from .tm_objects import TMObjects


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

                objects = []
                for line in lines:
                    objects.extend(extract_complete_json_objects(line))

                objs: TMObjects = TMObjects(filename_without_string)
                for obj in objects:
                    objs.analyze_object(obj)
                objs.display()
                objs.insert_objects(conn, filename_without_string)
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

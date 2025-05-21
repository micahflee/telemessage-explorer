# TeleMessage Explorer

TeleMessage Explorer is open source software for journalists and researchers to investigate the [TeleMessage dataset](https://github.com/micahflee/telemessage-explorer). You must have a copy of the TeleMessage dataset (which is only available to journalists and researchers) in order to use it.

This repo includes code to do the following:

- Loop through heap dump files searching for all valid JSON objects, and imports the relevant ones into a PostgreSQL database
- A user-friendly web app to explore this database

You'll need Docker, Python, and Poetry.

## Launch the containers

First, launch the containers:

```sh
docker compose up --build
```

You need to do this first because it spins up a PostgreSQL database. Next, follow the steps below to crunch the data.

If you've already crunched the data, load http://localhost:5173/ to access the web app. Both Flask and Vue are dev mode.

## Crunch the data

Extract `telemessage.7z`.

You'll end up with 2,729 files called `heapdump`, `heapdump.1`, `heapdump.2`, ..., `heapdump.2728`. The script expects all files to have a number at the end, so rename `heapdump` to `heapdump.0`:

```sh
cd path/to/extracted/dataset/
mv heapdump heapdump.0
```

Then run `strings` on each heap dump file (this takes a while) to extract the strings from them:

```sh
for F in $(ls); do echo $F; strings $F > ${F}.strings; done
```

When you're done, crunch the data like this:

```sh
cd cruncher

# Install dependencies
poetry install

# Set the database with environment variables (docker containers must be up)
export DB_NAME=db
export DB_USER=db
export DB_PASSWORD=db
export DB_HOST=localhost
export DB_PORT=54320

# Crunch the data
poetry run crunch --path path/to/heapdump-strings/
```

This script has a few other options:

```
$ poetry run crunch --help
Usage: crunch [OPTIONS]

Options:
  --path DIRECTORY       Path to folder with heap dump .strings files
                         [required]
  --num-threads INTEGER  Number of threads to run
  --num-skip INTEGER     Skip the first N heap dumps
  --help                 Show this message and exit.
```

Crunching the data will probably take several hours.

## When you're done crunching the data

In your Docker Compose terminal, press Ctrl-C to quick the containers.

Then start them again.

Access the web app from http://localhost:5173/.
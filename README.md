# TeleMessage Explorer

This repo includes code to do the following:

- Loop through heap dump files searching for all valid JSON objects, and imports the relevant ones into a PostgreSQL database
- A user-friendly web app to explore this database

You'll need Docker, Python, and Poetry.

## Launch the containers

First, launch the containers:

```sh
docker compose up --build
```

Next, follow the steps below to crunch the data.

If you've already crunched the data, load http://localhost:5173/ to access the web app. Both flask and vue are dev mode.

## Crunch the data

To start, extract `telemessage.7z`. Then run `strings` on each heap dump file (this takes a while) to extract the strings from them:

```sh
cd path/to/extracted/dataset/

# Rename the first file so it ends with a number, like the rest
mv heapdump heapdump.0

# Extract strings from heapdump files
for F in $(ls); do echo $F; strings $F > ${F}.strings; done
```

When you're done, start crunching like this:

```sh
cd cruncher

# Install dependencies
poetry install

# Set the database with environment variables (pointing to docker)
export DB_NAME=db
export DB_USER=db
export DB_PASSWORD=db
export DB_HOST=localhost
export DB_PORT=54320

# Crunch the data
poetry run crunch --path path/to/heapdump-strings/
```

There are a few other options to:

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
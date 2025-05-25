FROM python:3.12-bookworm

# Install deps and updates
RUN DEBIAN_FRONTEND=noninteractive && \
    export DEBIAN_FRONTEND && \
    apt-get update && \
    apt-get install -y libpq-dev python3-dev && \
    apt-get upgrade --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

WORKDIR /app

# Install python dependencies
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry install --no-root

# Copy everything else
COPY . .

# Execute
EXPOSE 80
ENV FLASK_APP=app
CMD ["poetry", "run", "flask", "run", "-h", "0.0.0.0", "-p", "8080"]

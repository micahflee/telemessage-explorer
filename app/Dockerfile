FROM python:3.12-bookworm

# Install deps and updates
RUN DEBIAN_FRONTEND=noninteractive && \
    export DEBIAN_FRONTEND && \
    apt-get update && \
    apt-get install -y libpq-dev python3-dev && \
    apt-get upgrade --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js from NodeSource repository
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install nodejs -y && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

WORKDIR /app

# Install python dependencies
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry install --no-root

# Copy the frontend
RUN mkdir frontend
COPY ./frontend/package.json frontend
COPY ./frontend/package-lock.json frontend

# Install node dependencies
RUN cd frontend && npm install

# Copy everything else
COPY . .

# Build the frontend
RUN cd frontend && npm install
# RUN cd frontend && npm run build
RUN cd frontend && npm run build -m development

# Execute
EXPOSE 80
ENV FLASK_APP=app
CMD ["poetry", "run", "flask", "run", "-h", "0.0.0.0", "-p", "8080"]

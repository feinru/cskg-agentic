FROM python:3.10-slim

WORKDIR /app

# Ensure Python output is immediately flushed to logs
ENV PYTHONUNBUFFERED=1

# Install curl and ca-certificates to download docker client
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz | tar -xz -C /tmp && \
    mv /tmp/docker/docker /usr/local/bin/ && \
    rm -rf /tmp/docker && \
    apt-get purge -y --auto-remove ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application
COPY . .

# Make the pipeline script executable
RUN chmod +x run.sh

CMD ["./run.sh"]

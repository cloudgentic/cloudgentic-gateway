FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for shutdown endpoint)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-26.1.4.tgz \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development
FROM base AS development
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8421", "--reload"]

# Production
FROM base AS production
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8421", "--workers", "4"]

FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /bin/uv

WORKDIR /app
COPY . /app

# psycopg2 ビルドに必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    && uv sync --dev \
    && apt-get purge -y build-essential libpq-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

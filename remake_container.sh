#!/bin/sh
direnv allow
docker compose down
docker compose build
docker compose up -d

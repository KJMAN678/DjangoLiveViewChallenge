#!/bin/sh
uv run manage.py migrate
uv run manage.py createsuperuser --noinput || true
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application

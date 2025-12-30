#!/bin/sh
uv run manage.py migrate
uv run manage.py createsuperuser --noinput || true
uv run manage.py runserver 0.0.0.0:8000

#!/bin/sh
# Run Cold Outreach Engine with Docker (one command).
# Pulls model from web on first run; model runs on <8GB RAM.
# Open http://localhost:8000 when ready.

cd "$(dirname "$0")"
docker compose up --build

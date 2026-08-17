#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/YuLaw/Yu-Law-AI-Workbench"
APP_DIR="$REPO_DIR/pythonanywhere-flask"
WSGI_FILE="/var/www/yulaw_pythonanywhere_com_wsgi.py"

git -C "$REPO_DIR" pull --ff-only origin main
cd "$APP_DIR"
python3.13 -m unittest discover -s tests -v
PYTHONPATH="$APP_DIR" python3.13 -c "from flask_app import app; assert app is not None"
touch "$WSGI_FILE"
git -C "$REPO_DIR" rev-parse --short HEAD

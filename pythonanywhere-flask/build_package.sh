#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_dir=$(CDPATH= cd -- "$package_dir/.." && pwd)
output_dir=$(CDPATH= cd -- "$repository_dir/.." && pwd)/outputs
output_file="$output_dir/yu-law-ai-workbench-pythonanywhere-flask.zip"

mkdir -p "$output_dir"
cd "$repository_dir"

python3 -m zipfile -c "$output_file" \
  pythonanywhere-flask/flask_app.py \
  pythonanywhere-flask/litigation_flask.py \
  pythonanywhere-flask/requirements.txt \
  pythonanywhere-flask/README-PythonAnywhere.md \
  pythonanywhere-flask/pythonanywhere_wsgi.py.example \
  pythonanywhere-flask/data \
  pythonanywhere-flask/templates \
  pythonanywhere-flask/static \
  workbuddy-pilot/case-management/case_manager \
  workbuddy-pilot/case-management/dashboard

printf '%s\n' "$output_file"

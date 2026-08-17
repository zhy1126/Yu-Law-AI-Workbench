#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_dir=$(CDPATH= cd -- "$package_dir/.." && pwd)
output_dir=$(CDPATH= cd -- "$repository_dir/.." && pwd)/outputs
output_file="$output_dir/yu-law-ai-workbench-pythonanywhere-flask.zip"

mkdir -p "$output_dir"
cd "$package_dir"

python3 -m zipfile -c "$output_file" \
  flask_app.py \
  requirements.txt \
  README-PythonAnywhere.md \
  pythonanywhere_wsgi.py.example \
  data \
  templates \
  static

printf '%s\n' "$output_file"

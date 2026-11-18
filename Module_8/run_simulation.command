#!/bin/zsh
# Offline Module 8 one-lump simulator. No serial port is used.
set -eu
module_dir="${0:A:h}"
project_dir="${module_dir:h}"
cd "$project_dir"
exec "$project_dir/.venv/bin/python" "$module_dir/python/run_simulation.py" "$@"

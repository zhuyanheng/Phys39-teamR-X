#!/bin/zsh
# Offline analysis viewer. Never opens the hardware connection.
set -eu
module_dir="${0:A:h}"
project_dir="${module_dir:h}"
cd "$project_dir"
exec "$project_dir/.venv/bin/python" "$module_dir/python/angstrom_analysis_gui.py" "$@"

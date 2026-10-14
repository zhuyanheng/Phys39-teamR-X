#!/bin/zsh
set -eu
module_dir="${0:A:h}"
project_dir="${module_dir:h}"
cd "$project_dir"
exec "$project_dir/.venv/bin/python" "$module_dir/python/pi_tec_control_gui.py" "$@"

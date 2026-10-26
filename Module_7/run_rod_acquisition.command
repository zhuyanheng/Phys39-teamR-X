#!/bin/zsh
# Module 7 six-channel rod acquisition GUI.
# Use --preview to open it without touching a serial port.
set -eu
module_dir="${0:A:h}"
project_dir="${module_dir:h}"
cd "$project_dir"
exec "$project_dir/.venv/bin/python" "$module_dir/python/module_07_rod_acquisition_gui.py" "$@"

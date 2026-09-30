#!/bin/zsh

set -u

project_dir="${0:A:h:h}"
python_bin="$project_dir/.venv/bin/python"
gui_script="$project_dir/Module_5/python/p_only_tec_control_gui.py"

if [[ ! -x "$python_bin" ]]; then
  print -u2 "Project Python environment not found: $python_bin"
  print -u2 "Create the .venv environment and install requirements.txt first."
  exit 1
fi

"$python_bin" "$gui_script"

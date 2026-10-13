#!/bin/zsh

set -eu

module_dir="${0:A:h}"
project_dir="${module_dir:h}"
python_bin="$module_dir/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  print -u2 "Project Python environment missing: $python_bin"
  print -u2 "The simulator requires a modern Python/Tk environment in Module_6/.venv."
  print -u2 "See Module_6/README.md; the system Tk 8.5 can show an empty window."
  exit 1
fi

cd "$project_dir"
exec "$python_bin" "$module_dir/python/run_simulation.py" "$@"

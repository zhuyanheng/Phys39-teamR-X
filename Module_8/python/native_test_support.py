"""Compile the actual firmware on a host for hardware-free integration tests."""
from functools import lru_cache
from pathlib import Path
import shutil
import subprocess
import tempfile
import atexit

MODULE=Path(__file__).resolve().parents[1]
_TEMP=tempfile.TemporaryDirectory(prefix='module8-native-')
atexit.register(_TEMP.cleanup)

@lru_cache(None)
def executable(name):
    compiler=shutil.which('clang++') or shutil.which('g++')
    if not compiler:raise RuntimeError('C++ compiler required for firmware tests')
    output=Path(_TEMP.name)/name
    subprocess.run([compiler,'-std=c++11','-Wall','-Wextra','-Werror',
                    str(MODULE/'python/tests_native'/f'{name}.cpp'),'-o',str(output)],check=True,capture_output=True,text=True)
    return output

def firmware(commands):
    result=subprocess.run([str(executable('firmware_harness'))],input='\n'.join(commands)+'\n',capture_output=True,text=True,check=True)
    return result.stdout.splitlines()

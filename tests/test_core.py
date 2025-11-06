import subprocess
import os

def test_python_starts():
    assert subprocess.call(["python", "--version"]) == 0

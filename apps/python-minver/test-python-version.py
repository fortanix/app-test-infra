#!/usr/bin/python3

import os
import sys
PYTHON_MIN_VER_MJ = 3
PYTHON_MIN_VER_MN = 9

if sys.version_info.major < PYTHON_MIN_VER_MJ:
    print(f"FAILED: Python major version is too low: {sys.version_info.major}.{sys.version_info.minor}")
    exit(1)

if sys.version_info.minor < PYTHON_MIN_VER_MN:
    print(f"FAILED: Python minor version is too low: {sys.version_info.major}.{sys.version_info.minor}")
    exit(2)

print(f"SUCCESS: Python version ({sys.version_info.major}.{sys.version_info.minor}) is equal to or greater than the minimum expected {PYTHON_MIN_VER_MJ}.{PYTHON_MIN_VER_MN}.")

exit(0)

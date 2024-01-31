#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
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

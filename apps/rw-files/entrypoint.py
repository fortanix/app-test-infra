#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#
# Test to check which files require read-write permissions on it
# by default, rather than read-only.
#
# List directories and files recursively of the input path provided
#
import os


def open_all(path):
    if path is None:
        return
    for parent, dirs, files in os.walk(path):
        for fname in files:
            abs_path = os.path.join(parent,fname)
            print(abs_path)
            with open(abs_path, 'rb') as f:
                f.read()

open_all('/etc')

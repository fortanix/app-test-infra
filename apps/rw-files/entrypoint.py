#!/usr/bin/python3

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

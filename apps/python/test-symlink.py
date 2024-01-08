#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os

TMP_FILE="/f1.txt"
TMP_SYMLINK="/tmp/s1"
FILE_DATA="hello-world"

an = os.getcwd()+TMP_FILE
f = open(an, "a")
f.write(FILE_DATA)
f.close()

os.symlink(an, TMP_SYMLINK)

f = open(TMP_SYMLINK, "r")
read_data = f.read()

if (read_data == FILE_DATA):
    print('test-symlink passed')
f.close()

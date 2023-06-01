#!/usr/bin/python3

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

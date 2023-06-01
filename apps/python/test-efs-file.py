#!/usr/bin/python3

import os

# The python random module does not produce cryptographically strong randomness.
# For this test's purposes, that is fine. We mostly just want data that's not
# all zeroes.

# Write 8KB at a time, to avoid using up too much memory at once.
write_size = 8 * 1024 * 1024

# 9 GB file. This should be more than 4G (so the file size won't fit in
# 32 bits). 9 is not a power of 2, so possibly may be more stressful
# than testing 8 GB.
file_size = 9 * 1024 * 1024 * 1024

test_file = '/tmp/test-data'

written = 0

data = os.urandom(write_size)

with open(test_file, 'wb') as fh:
    fd = fh.fileno()

    while written < file_size:
        fh.write(data)
        written += write_size
        # ZIRC-5255 regression test: lseek() on EFS files was not working
        # for offsets greater than 2GB.
        offset = os.lseek(fd, 0, os.SEEK_CUR)
        if offset != written:
            raise Exception('lseek offset did not match expected offset')

result = os.stat(test_file)
if result.st_size != file_size:
    print('File size did not match. Expected {} actual {}'.format(file_size, result.st_size))
    exit(1)

print('test-efs-file passed')
exit(0)

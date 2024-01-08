#!/usr/bin/env python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os
import random
import string
import subprocess

random_data_len = 1024
random_data = ''.join(random.choice(string.ascii_lowercase) for i in range(random_data_len))
RO_FILE='/root/testfile'
RO_FILE_DATA='This is a testfile\n'
RW_FILE='/root/testfile2'
RW_FILE_RESTART='/root/testfile3'
RW_FILE_RESTART_DATA='ysmkscyynewuwjdnclkvaxdxzuatsxpymjgfrmkedoajsnglxwvgmyzxlomgaofqwruwdaoctfsfsdsmbitbtvcvvxjzoylrzaxndyjyjsxqyngsvuaoqlqsindfzhpaflqfwmdusovdjxkxdxbbdlwwxegvjxdxexwlzebvcwgzvcpfeejuftkaszbfkqwqgafiiszkrgjjhqurlqswjtqkpmekmrqqsxrqfaxbdfbcuhwypyeofcymilmiansiryzxzizfyutovrxuxxomsnbhqvshmmpuabwmghgmydsmejiaykhhhesmdzgmsvmxzehwzfnljfnbaxrgevykootjtqnunnygjgjyzmoavngryqumojxopqdxzxncypzeoxhhnjhatfusbiugrqclksyghktlkytspbmyyqratffivuchcqkiqsyeggkdiocworcydivbvgkolrfwonivsbtcemsmjkomdccsjaebtwbtaydcuszhexvrprjlmejilgeehcvalupxuybpjhimgkssbdigjqkaybeuzfvtskisbwahxlkmvpwicxhujhhgyustmowhyaxaivbwrcisejgxlcwwnijktzrfpnouqcvscciivhljydbofumiaclclzlacdoiplnxmnclcjswtzokwibftpfgclegkhbacdfrlydajfazfozfmysroaoluafelvofgnikqnksbptzvgpkhgtjwxnlrvlmoqmijxjizsqavgboeidtkmvtscighkvwusjkknmeabdpwzunelvirnafxafjghplglwosspkffrrobnxbaiukrklzwmngfjfhtmizmzxchwwjnkrhxkkpkncprzrhonkxxlxxypfakufeqiruzcvicwblqinnriiwihlfupqbbbaqgildmvnvhowqsjqafybrbidknjjgplohjbstaddpogtscyckmyozabxgoyjuzudckqkxnklfgkxwtmpudklogxhpxtqmtatdusjnqmxbnhbiyit'

def generate_data(testfile=RW_FILE, testdata=None, display=False):
    global random_data
    if testdata is None:
        testdata = random_data
    with open(testfile, 'wb') as f:
        f.write(bytearray(testdata, 'utf-8'))
        if display:
            print('Generated data={}'.format(testdata))

def read_data(testfile=RW_FILE):
    global random_data_len
    with open(testfile, 'rb') as f:
        data = f.read()
        if len(data) != random_data_len:
            print(' data read is not {} bytes, obtained {} bytes'.format(random_data_len, len(data)))
        return data

def compare_data(testfile=RW_FILE, expected_data=None):
    read = read_data(testfile)
    if expected_data is None:
        expected_data = random_data
    if bytearray(expected_data, 'utf-8') != read:
        print('Expected data={}'.format(expected_data))
        print('Obtained data={}'.format(str(read)))
        raise ValueError('File {} does not contain expected data'.format(testfile))
    else:
        print('File {} contains expected data'.format(testfile))

def flush_cache():
    try:
        out = subprocess.check_output('/root/flushcache.sh')
        if out.strip() != b'Dropped filesystem cache':
            raise ValueError('Unable to flush FS cache')
    except subprocess.CalledProcessError as e:
        raise ValueError('{} : {}'.format(e.output, e.returncode))

def read_data_from_ro_layer():
    with open(RO_FILE, 'r') as f:
        data = f.read()
    if RO_FILE_DATA != data:
        raise ValueError('Unexpected data from RO layer: {} Expected: {}'.format(data, RO_FILE_DATA))
    else:
        print('RO layer testfile contains expected data')

# Test 1 - Read data from a pre-existing file
# This ensures we are able to read from the RO layer
# of the nitro enclave filesystem
print('Start Test 1')
read_data_from_ro_layer()
print('### Test 1 complete ###')

# Test 2 - Create a new file with random data. This
# file would be present in the RW layer of the enclave.
# Flush the kernel filesystem cache so that any new data
# is flushed to the read-write block device in the
# parent image. Attempt to read the same file again, this
# will require the enclave to fetch the data from the
# block device.
print('Start Test 2')
generate_data()
flush_cache()
read_data()
compare_data()
print('### Test 2 complete ###')

# Test 3 - This is similar to test 2 except that the RW layer is
# verified across enclave restarts. This test would create
# RW_FILE_RESTART only on the first run i.e. if it doesn't exist. When
# it is created, it would print the contents to console.
# If the file already exists, then it would compare if the
# expected data is present.
print('Start Test 3')
if os.path.exists(RW_FILE_RESTART):
    compare_data(RW_FILE_RESTART, RW_FILE_RESTART_DATA)
    print('### Test 3 part 1 complete ###')
else:
    generate_data(RW_FILE_RESTART, testdata=RW_FILE_RESTART_DATA, display=True)
    compare_data(RW_FILE_RESTART, RW_FILE_RESTART_DATA)
    print('### Test 3 part 2 complete ###')


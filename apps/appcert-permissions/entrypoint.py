#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os

print('Guest application >> uid = {} gid = {}'.format(os.getuid(), os.getgid()))
print('Attemping to access CA and application certificates...')

print(os.stat('/opt/fortanix/enclave-os/app-config/rw/cacert.pem'))
#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os

if os.path.exists('/opt/fortanix/enclave-os/default_cert/app_private.pem') and \
   os.path.exists('/opt/fortanix/enclave-os/default_cert/app_public.pem'):
   print('Key and cert file exist for default certs')
else:
    raise ValueError('Either key or cert file don\'t exist for default certs')

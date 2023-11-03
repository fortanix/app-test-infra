#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
import os

if os.path.exists('/opt/fortanix/enclave-os/default_cert/app_private.pem') and \
   os.path.exists('/opt/fortanix/enclave-os/default_cert/app_public.pem'):
   print('Key and cert file exist for default certs')
else:
    raise ValueError('Either key or cert file don\'t exist for default certs')

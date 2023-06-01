#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
import os

if os.path.exists('/ftx-efs/key.pem') and \
   os.path.exists('/ftx-efs/cert.pem'):
   print('Key and cert file exist')
else:
    raise ValueError('Either key or cert file don\'t exist')

#!/usr/bin/python3
import os

print('Guest application >> uid = {} gid = {}'.format(os.getuid(), os.getgid()))
print('Attemping to access CA and application certificates...')

print(os.stat('/opt/fortanix/enclave-os/app-config/rw/cacert.pem'))
#!/usr/bin/python3
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os

DEFAULT_CERT_DIR = "/opt/fortanix/enclave-os/default_cert"
DEFAULT_KEY_FILE = "app_private.pem"
DEFAULT_CERT_FILE = "app_public.pem"

key_path = os.path.join("", DEFAULT_CERT_DIR, DEFAULT_KEY_FILE)
cert_path = os.path.join("", DEFAULT_CERT_DIR, DEFAULT_CERT_FILE)

from OpenSSL.crypto import (FILETYPE_PEM, dump_publickey, load_certificate,
                            load_privatekey)

with open(cert_path) as cert_f:
    cert = load_certificate(FILETYPE_PEM, cert_f.read())

with open(key_path) as key_f:
    key = load_privatekey(FILETYPE_PEM, key_f.read())

cert_pub = dump_publickey(FILETYPE_PEM, cert.get_pubkey())
key_pub= dump_publickey(FILETYPE_PEM, key)
if cert_pub != key_pub:
    raise ValueError('Certificate and private key\'s public keys don\'t match')

print('Python Default Certificate Test Successful')
exit(0)

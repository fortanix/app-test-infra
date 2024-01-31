#!/usr/bin/bash -exu
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
set -o pipefail

#
# Download the published version of enclaveos-signer from github and set up a
# python virtual environment for running it.
#

# Remove any copy of the public repository from a previous test run.
/usr/bin/rm -rf enclaveos-signer
/usr/bin/git clone https://github.com/fortanix/enclaveos-signer.git
cd enclaveos-signer

# Create a Python virtual environment for installing the signer's
# dependencies and running it.
/usr/bin/python3 -m venv signer-test
source signer-test/bin/activate
/usr/bin/pip3 install -r requirements.txt

/usr/bin/chmod +x enclaveos-signer


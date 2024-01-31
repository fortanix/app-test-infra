#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
echo -e "$1    $2\n" > /etc/hosts
/opt/fortanix/enclave-os/bin/enclaveos-runner /opt/fortanix/enclave-os/manifests/app.manifest.sgx
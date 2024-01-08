#!/usr/bin/bash -exu
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
set -o pipefail

source enclaveos-signer/signer-test
enclaveos-signer/enclaveos-signer "$@"

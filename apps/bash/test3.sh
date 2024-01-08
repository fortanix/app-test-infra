#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
set -eo pipefail

(echo "Printed to fd 1" >&1) | grep -q '^Printed'
(echo "Printed to fd 2" >&2) 2>&1 | grep -q '^Printed'

# The devices always map to the enclaveos-runner streams (ZIRC-1233), we
# can't capture them with redirection.
echo "Printed to /dev/stdout" > /dev/stdout
echo "Printed to /dev/stderr" > /dev/stderr

echo "test3 passed"

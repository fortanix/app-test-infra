#!/bin/bash -ex
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
set -o pipefail

if sync && echo 3 > /proc/sys/vm/drop_caches ; then
        echo "Dropped filesystem cache"
        exit 0
else
        echo "Failed to flush filesystem cache"
        exit 1
fi


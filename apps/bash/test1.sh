#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
if [ "$(/root/test2.sh)" = "Output from child process" ] && [ "$(/root/test5.sh)" = "test 5 passed" ]; then
    echo "test1 passed"
else
    echo "test1 failed"
fi

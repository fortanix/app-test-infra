#! /bin/bash
# NOTE: The space after the shebang above is an intentional element of this test case.
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


echo "Output from child process"

# Workaround for ZIRC-144: don't exit while test1.sh is starting the second
# process in the pipeline. We can't use `sleep` because of ZIRC-145.
n=0
while [ $n -lt 1000000 ]; do
    n=$[$n + 1]
done

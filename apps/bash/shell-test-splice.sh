#!/bin/bash -e
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This invocation exercises a path that cases grep to use the splice
# call. As best as we can determine, all of these conditions must be true
# for grep to use splice:
# 1. The output of some command must be piped to grep. It won't use splice
#    if grep is operating on a file, or even if grep's stdin is redirected
#    from a file.
# 2. Grep must find at least one match in the input data.
# 3. Grep's stdout must be redirected to a special file like /dev/null.
#    Redirecting to a regular file won't work.

cat /etc/passwd | grep root > /dev/null

echo "shell-test-splice passed"

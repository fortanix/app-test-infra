#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test for running with a python installation that requires glibc 2.28
# or newer. glibc 2.28 added several new symbols, including fcntl64,
# which is used by Python. If you run with an older glibc, the dynamic
# loader will fail to resolve the fcntl64 symbol in glibc, and the
# program will terminate without returning from the python fcntl() call.
# So if fcntl returns at all, this test has passed.
#
# Note that if the symbol resolves, but the fcntl call fails for some
# other reason, the python fcntl function will raise an OSError exception,
# which will also cause the test to fail.

import fcntl

flags = fcntl.fcntl(0, fcntl.F_GETFL)
print('flags are {:x}'.format(flags))
print('fcntl test passed')

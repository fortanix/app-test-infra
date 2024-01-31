#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
times=$1
[ $times -gt 0 2> /dev/null ] || times=300

for (( c=1; c<=$times; c++ ))
do
	echo "hello $c"
	cp somefile testdir/somefile
	rm -rf testdir/somefile
	ls testdir/
	cat somefile > testdir/x
	date
done > OUTPUT

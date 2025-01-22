#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# Check that "_" is empty before executing any commands
echo $_
if [[ -n $_ ]]; then
  echo "test7 failed"
  exit 1
fi

env

if [[ $_ == *"env" ]]; then
  echo "test7 passed"
else
  echo "test7 failed"
fi

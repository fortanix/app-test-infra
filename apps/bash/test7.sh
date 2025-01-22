#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# Original value of "_" should point to this binary (bash)
if [[ ! $_ == *"/bin/bash" ]]; then
  echo $_
  echo "test7 failed"
  exit 0
fi

env
if [[ $_ == *"env" ]]; then
  echo "test7 passed"
else
  echo "test7 failed"
fi

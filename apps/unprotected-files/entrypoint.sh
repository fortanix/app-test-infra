#!/usr/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#
# Entrypoint script for the UnprotectedFiles guest app.
#

ls -al /
cat /.dockerenv
cat /.dockerinit
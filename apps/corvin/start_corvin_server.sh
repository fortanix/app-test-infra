#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# finally run the scripts
/emsaas/utils/start.sh --with-node-agent --no-expire /emsaas/scripts/workflow_eos.sh /root/build.json /root/app.json

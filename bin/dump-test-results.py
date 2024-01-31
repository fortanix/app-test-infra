#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import argparse
from test_utils import TestResults

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump test results')
    parser.add_argument('--run-id', help='Test run identifier')
    parser.add_argument('--output', '-o', help='Output file')
    args = parser.parse_args()

    with open(args.output, 'w') as fh:
        TestResults.dump(fh, args.run_id)

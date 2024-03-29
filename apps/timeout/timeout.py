#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This test only exercises the test framework timeout mechanism and verifies
# that it works.

import time
from test_app import TestApp, main
from test_utils import TimeoutException


class TestTimeout(TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestTimeout, self).__init__(run_args, [])

    # We set a very short timeout so we can verify if overriding the default
    # timeout works. This timeout gets multiplied by 3 in SGX, so we set
    # it very low.
    def get_timeout(self):
        return 5

    def run(self):
        try:
            time.sleep(60)
            print('Test failed. Timeout not raised within 60 seconds')
            return False
        except TimeoutException:
            print('Test succeeded. Timeout raised within 60 seconds')
            return True

if __name__ == '__main__':
    main(TestTimeout)

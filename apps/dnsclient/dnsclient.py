#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import test_app


class TestDnsClient(test_app.TestApp):
    def run(self):
        container = self.container('zapps/dnsclient', memsize='128M')
        container.prepare()
        container.run_and_compare_stdout(['127.0.0.1', '127.0.0.1', '127.0.0.1'])
        return True

if __name__ == '__main__':
    test_app.main(TestDnsClient)

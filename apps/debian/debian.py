#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import argparse
import test_app


class TestDebian(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestDebian, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Debian test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        # Regression test for ZIRC-2366
        container = self.container('debian', registry='library', memsize='128M',
                                   image_version='10',
                                   entrypoint=['/usr/bin/getent', 'hosts', 'fortanix.com'])
        container.prepare()
        logs = container.run_and_return_logs()
        if any([line.endswith('fortanix.com') for line in logs.stdout]):
            self.result('debian', 'PASSED')
        else:
            self.result('debian', 'FAILED')

        return True

if __name__ == '__main__':
    test_app.main(TestDebian)

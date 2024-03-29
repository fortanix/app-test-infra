#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test for using a symbol from glibc 2.28 in python in a debian
# buster (10.x) container.
#

import test_app


class TestPythonBuster(test_app.TestApp):
    def __init__(self, run_args, _):
        super(TestPythonBuster, self).__init__(run_args, [])

    def run(self):
        container = self.container('python', memsize='256M', registry='library', image_version='3.8.2-buster', rw_dirs=['/'],
                                   entrypoint=['/root/fcntl.py'])
        container.prepare()
        container.copy_file('fcntl.py', '/root')
        return container.run_and_search_logs('fcntl test passed')

if __name__ == '__main__':
    test_app.main(TestPythonBuster)


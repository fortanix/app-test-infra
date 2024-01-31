#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os
import test_app


class TestPythonScipy(test_app.TestApp):
    def run(self):
        container = self.container(
            'zapps/python-scipy', memsize='2G', rw_dirs=['/'], thread_num=512)
        container.prepare()
        container.run()
        container.wait()
        container.stop()
        return True

    def get_timeout(self):
      if os.environ.get('PLATFORM', 'linux') == 'sgx':
        return 4 * 60 * 60
      else:
        return 1 * 60 * 60

if __name__ == '__main__':
    test_app.main(TestPythonScipy)

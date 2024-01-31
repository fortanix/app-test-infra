#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import test_app


class TestPythonPandas(test_app.TestApp):
    def run(self):
        container = self.container('zapps/python-pandas', memsize='512M', rw_dirs=['/'])
        container.prepare()
        container.run()
        container.wait()
        container.stop()
        return True

if __name__ == '__main__':
    test_app.main(TestPythonPandas)

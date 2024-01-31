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


class TestIozone(test_app.TestApp):
    def run(self):
        container = self.container('zapps/iozone', memsize='512M', rw_dirs=['/iozone_rw', '/tmp'])
        container.prepare()
        container.run()
        container.wait()
        cwd = os.getcwd()
        container.copy_file_from_container("/tmp/iozone_out_rw.wks", "{}/iozone_out_rw.wks".format(cwd))
        container.copy_file_from_container("/tmp/iozone_out_ro.wks", "{}/iozone_out_ro.wks".format(cwd))
        container.stop()
        with open('logs/{}.stdout.0'.format(container.name)) as f:
            to_print = 0
            is_ro = 0
            for line in f:
                if 'Auto Mode' in line:
                    if not is_ro:
                        print('fs_rw without integrity protection output:')
                        is_ro = 1
                    else:
                        print('fs_ro with integrity proection output:')
                    to_print = 1
                elif 'iozone test complete' in line:
                    to_print = 0
                    print('\n')
                if to_print:
                    print(line, end='')
        return True

if __name__ == '__main__':
    test_app.main(TestIozone)

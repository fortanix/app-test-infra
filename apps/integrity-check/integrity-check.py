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


class FSIntegrityCheck(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(FSIntegrityCheck, self).__init__(run_args, [])

    def run(self):
        container = self.container('zapps/python',
                                    entrypoint=['/root/run-test.sh'],
                                    ro_dirs=['/opt/fortanix/enclave-os/app-config/ro',],
                                    rw_dirs=['/opt/fortanix/enclave-os/app-config/rw',],
                                    memsize="512M", nitro_memsize="2048M", thread_num=16 )
        container.copy_to_input_image(['run-test.sh'], '/root/')
        container.prepare()
        container.run()
        container.wait(expected_status=0) # raises exception on error
        return True


if __name__ == '__main__':
    test_app.main(FSIntegrityCheck)

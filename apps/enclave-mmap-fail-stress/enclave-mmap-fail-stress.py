#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os
import stat
import test_app


class TestEncMmap(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestEncMmap, self).__init__(run_args, [])

    ISGX = "/dev/isgx"
    ISGX_FLC = "/dev/sgx"
    DCAP = "/dev/sgx/enclave"
    IN_KERNEL = "/dev/sgx_enclave"

    def GetDeviceType(self):
        possible_devices = [self.ISGX, self.DCAP, self.ISGX_FLC, self.IN_KERNEL]

        for device in possible_devices:
            try:
                statbuf = os.lstat(device)
                if stat.S_ISCHR(statbuf[stat.ST_MODE]):
                    return device

            except Exception:
                pass

    def run(self):
        manifest_options = {'stress.mmap_fail_during_enclave_init' : '1'}

        device = self.GetDeviceType()

        print("Testing with device " + device)

        errno = 12
        output_lines = ['mmap failed at low address 0(0x0) with errno = ']

        if (device == self.DCAP or device == self.IN_KERNEL):
            errno = 17
            output_lines = ['mmap failed at low address 65536(0x10000) with errno = ']
        elif (device == self.ISGX or device == self.ISGX_FLC):
            errno = 12
            output_lines = ['mmap failed at low address 0(0x0) with errno = ']
        else:
            print('No device')
            raise

        output_lines[0] = output_lines[0] + str(errno) + '.'


        container = self.container('zapps/python', memsize='512M', image_version='2020112709-cd72bb3',
                                   entrypoint=[
                                       '/usr/bin/python3', '--version'],
                                   manifest_options=manifest_options,
                                   zircon_panic_expected=True,
                                   expected_status=1
                                   )
        container.prepare()

        return container.run_and_search_logs(output_lines[0])


if __name__ == '__main__':
  test_app.main(TestEncMmap)

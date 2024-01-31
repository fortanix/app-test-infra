#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import test_app


class TestIoctl(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestIoctl, self).__init__(run_args, [])

    def run(self):
       
        manifest_options = {'stress.ioctl_fail_during_enclave_init' : '1'}
        # This message should be exactly same as the log message in 
        # zircon/pal/src/sgx/urts/urts-driver.h IoctlWithRetries() function
        msg = 'DriverIoctl failed with status = -1. Retry attempt '
        
        # The value of num_failures should be same as STRESS_IOCTL_FAILURE_LIMIT 
        # macro in zircon/pal/src/sgx/urts/urts-driver.h
        num_failures = 3
        output_lines = []
        
        for i in range(num_failures):
            output_lines.append(msg + str(i+1))
        
        container = self.container('zapps/python', 
                                   memsize='128M', 
                                   image_version='2020112709-cd72bb3',
                                   entrypoint=[
                                              '/usr/bin/python3', 
                                              '--version'
                                              ],
                                   manifest_options=manifest_options
                                  )
        container.prepare()

        return container.run_and_search_multiple_lines_logs(output_lines)

if __name__ == '__main__':
  test_app.main(TestIoctl)

#!/usr/bin/python3
#
# Copyright (C) 2023 Fortanix, Inc. All Rights Reserved.
#
# Test that checks if hostname is present inside an enclave and
# if it properly resolves to an IP address

import test_app
import time


class TestHostname(test_app.TestApp):
    def run(self):
        container = self.container('zapps/python-web-server', image_version='2023021014-868084a',
                                   entrypoint=['/root/test-hostname.py'],
                                   container_env=['ALLOW_EMPTY_PASSWORD=yes',
                                                  'ENCLAVEOS_DEBUG=debug',
                                                  'RUST_LOG=debug',
                                                  'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE=true'],
                                   memsize="2048M" )
        container.copy_to_input_image(['test-hostname.py'], '/root/')
        container.prepare()

        return container.run_and_compare_stdout(['test-hostname passed'])

if __name__ == '__main__':
    test_app.main(TestHostname)

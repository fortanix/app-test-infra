#!/usr/bin/python3
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test using ubuntu container to check if default app certs are installed
# in the correct location
import ccm_util
import os
import test_app


class TestPythonDefaultAppcert(test_app.TestApp):

    def __init__(self, run_args, test_arg_list):
        super(TestPythonDefaultAppcert, self).__init__(run_args, [])

    def run(self):
        node_url = os.getenv('NODE_AGENT', 'http://0.0.0.0:9092/v1')

        if os.getenv('PLATFORM', 'nitro') == 'nitro':
            container_env = { 'NODE_AGENT' : node_url, 'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE' : None }
        else:
            container_env = { 'NODE_AGENT_BASE_URL' : node_url }

        container = self.container('python', memsize='512M', nitro_memsize='2G',
                                   image_version='3.9.5',
                                   registry='library',  network_mode='bridge',
                                   container_env=container_env, rw_dirs=['/root'],
                                   entrypoint=['/root/entrypoint.sh'])
        container.copy_to_input_image(['./entrypoint.sh', 'test-default-certs.py'], '/root/')
        container.prepare()

        ccm_instance = ccm_util.CCM()
        ccm_instance.create_app_register_build(container.get_image_metadata(), container.name)
        
        container.run()
        container.wait(expected_status=0)

        ccm_instance.cleanup_app(container.name)
        return True

if __name__ == '__main__':
    test_app.main(TestPythonDefaultAppcert)

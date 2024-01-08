#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test for re-signing converted applications using the published version of the
# signer. https://fortanix.atlassian.net/wiki/spaces/ZIR/pages/2277834786/Signing+EnclaveOS+Containers
#
# This test exercises converting a container with the current version of
# the converter, re-signing the container with the published version
# of the signer, and then running that container. This helps test that
# we don't inadvertently break the published signer with changes to the
# converter.

import subprocess
import test_app

TEST_MSG = 'signer published test passed'

class SignerPublishedTest(test_app.TestApp):
    def __init__(self, run_args, _):
        super(SignerPublishedTest, self).__init__(run_args, [])


    def run(self):
        # Get the signer from the public github repository and set it up.
        subprocess.check_call(['./set-up-signer.sh'])

        container = self.container('ubuntu', memsize='256M', registry='library',
                                   image_version='20.04',
                                   entrypoint=['/usr/bin/echo', TEST_MSG])
        container.prepare_image()
        signed = self.re_sign_image(input_image=container.converted_image,
                                    signer='enclaveos-signer/enclaveos-signer')

        # TODO: Add support for Kubernetes environments.
        signed_container = test_app.ZirconDockerContainer('ubuntu', memsize='256', registry='library',
                                                          converted_image=signed,
                                                          run_args=self.run_args,
                                                          skip_converter_version_check=True)
        signed_container.prepare_container()
        logs = signed_container.run_and_get_logs()
        if any([TEST_MSG in line for line in logs.stdout]):
            return True
        else:
            return False

if __name__ == '__main__':
    test_app.main(SignerPublishedTest)

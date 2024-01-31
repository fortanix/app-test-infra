#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This test exercises converting a container and then re-signing that
# container with various signer options, and then verifies that the the
# re-signed container can run. (Some of the cases involve scenarios where
# we expect that the app won't be able to run, like only having an sgx2
# signature but trying to run on sgx1 hardware).
#
# This test exercises the signer. Since only converted applications use
# the signer, running with --container-env=native or container-env=native-k8s
# doesn't make sense.

import test_app
import test_utils
import traceback


class SignerTest(test_app.TestApp):
    def __init__(self, run_args, _):
        super(SignerTest, self).__init__(run_args, [])

    def expect_model(self, expected=None, actual=None):
        if expected != actual:
            raise Exception('Actual memory model {} did not match expected model {}'.format(actual, expected))


    # Re-sign the input container with the specified memory model and verify that the newly
    # signed app runs in the expected mode (or doesn't run if the app was re-signed for SGX2
    # only and the host doesn't support SGX2).
    #
    # Returns True if the test case succeeded and False if it did not.
    def run_resigned(self, input_image=None, memory_model='all'):
        try:
            signed1 = self.re_sign_image(input_image=input_image.converted_image, memory_model=memory_model)

            # TODO: Add support for Kubernetes environments.
            signed1_container = test_app.ZirconDockerContainer(test_app.BASE_UBUNTU_CONTAINER, memsize='128M', registry='library',
                                                               converted_image=signed1, run_args=self.run_args)
            signed1_container.prepare_container()

            # TODO: Check that container produced the expected stdout.
            signed1_container.run()
            signed1_container.wait(ignore_status=True)

            signed1_logfile = signed1_container.save_log_file()

            actual_model = None
            with open(signed1_logfile) as fh:
                for line in fh.readlines():
                    if 'Loading enclave with memory model =' in line:
                        actual_model = line.split('=', 1)[1].strip()

            if memory_model == 'all':
                # Container should have signatures for both layouts, so we expect that it should run with
                # the best supported mode.
                if test_utils.sgx2_supported():
                    expected_model = 'minimal'
                else:
                    expected_model = 'full'
            elif memory_model == 'sgx1':
                expected_model = 'full'
            elif memory_model == 'sgx2':
                # If the host doesn't support SGX2, and we only have the SGX2 signature, we don't
                # expect the container to run.
                if not test_utils.sgx2_supported():
                    if actual_model is not None:
                        raise Exception('sgx2-only container ran on sgx1-only host')
                    else:
                        return True

                expected_model = 'minimal'

            self.expect_model(expected=expected_model, actual=actual_model)

        except Exception:
            print('run_resigned test case for memory model {} failed\n'.format(memory_model))
            traceback.print_exc()
            return False

        return True


    def run(self):
        base_container = self.container(test_app.BASE_UBUNTU_CONTAINER, memsize='128M', registry='library',
                                        image_version=test_app.BASE_UBUNTU_VERSION,
                                        entrypoint=['/bin/bash', '-c', 'echo Signer test container ran'])

        # TODO: Set entrypoint for bash container to run something simple like echo.

        # In this test, we don't really care about running the initial converted container. We have other
        # tests that exercise whether the converted container works. We just need the converted image, so
        # we can call the signer on the converted image. We'll then try running the re-signed image.
        base_container.prepare_image()
        print('Converted image id is {}'.format(base_container.converted_image))

        success = True

        success = self.run_resigned(input_image=base_container, memory_model='all') and success
        success = self.run_resigned(input_image=base_container, memory_model='sgx1') and success
        success = self.run_resigned(input_image=base_container, memory_model='sgx2') and success

        return success

if __name__ == '__main__':
    test_app.main(SignerTest)

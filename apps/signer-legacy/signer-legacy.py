#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.c
#
# Test for re-signing old containers with newer versions of the
# enclaveos-signer tool. We publish enclaveos-signer to a public github
# repository to give customers a method for production-signing their
# converted containers with their own keys. There may be situations where
# customers have containers they converted with older builds of zircon,
# but are using a newer version of enclaveos-signer. enclaveos-signer should
# support re-signing containers produced with older builds. This test
# helps ensure that we maintain that compatibility.
#
# The test uses already-converted images in ECR. We re-sign them with the
# current version of enclaveos-signer (from the source tree), and then verify
# that the re-signed container still runs.
#
# This test needs to be updated any time there is a major change to the
# way signatures are handled. Currently there are two major formats. For
# each of these formats, there is an associated converted image in ECR that
# will be tested.
#
# 513076507034.dkr.ecr.us-west-1.amazonaws.com/development-images/zircon-legacy-image:sgx1
# This container is signed with our original format. The only signature
# on this container is the signature for the SGX1 layout. The signer should
# re-sign with just an SGX1 signature. The resulting container should run
# on both SGX1 and SGX2 hardware, but it won't take advantage of SGX2 features.
#
# 513076507034.dkr.ecr.us-west-1.amazonaws.com/development-images/zircon-legacy-image:sgx2
# This container is signed with our SGX1+SGX2 format. This format has signatures
# for both SGX1 and SGX2 memory layout. The signer should re-sign with
# both signatures, and the re-signed container should run with SGX1 features
# on SGX1 hardware and SGX2 features on SGX2 hardware.

import docker
import test_app


class SignerLegacyTest(test_app.TestApp):
    def __init__(self, run_args, _):
        super(SignerLegacyTest, self).__init__(run_args, [])

         # The list of legacy containers that we need to test with.
        self.legacy_images = [
            # For now, the default behavior of the signer is to only sign with SGX1 signatures. This is to maintain
            # compatibility with the old version of the signer to give customers a chance to update their workflows
            # before we change the default behavior of the signing tool. Eventually, we will require customers
            # that only want SGX1 signatures to specifically request this. When this happens, we will need to update
            # this test case to explicitly pass sgx1 as the memory model.
            ('513076507034.dkr.ecr.us-west-1.amazonaws.com/development-images/zircon-legacy:sgx1', None),

            # Image signed with both SGX1 and SGX2 memory layouts.
            ('513076507034.dkr.ecr.us-west-1.amazonaws.com/development-images/zircon-legacy:sgx1sgx2', 'all')
        ]
        self.docker_client = docker.from_env()

    def run_resigned(self, input_image=None, memory_model='all'):
        print('Pulling image {} (this may take some time)'.format(input_image))
        try:
            (image_name, image_tag) = input_image.rsplit(':', 1)
            self.docker_client.images.pull(image_name, tag=image_tag)
        except Exception:
            print('\n\n\n****** Unable to pull image {} ******'.format(self.final_image))
            print('Possible causes are the image does not exist on the registry,')
            print('a misspelled image name, or you are not connected to the VPN.')
            print('Attempting to run with local image\n\n\n')
            # deliberately do not reraise

        signed = self.re_sign_image(input_image, memory_model=None)

        # TODO: Add support for Kubernetes environments.
        signed_container = test_app.ZirconDockerContainer(test_app.BASE_UBUNTU_CONTAINER, registry='library',
                                                          converted_image=signed, run_args=self.run_args,
                                                          skip_converter_version_check=True)
        signed_container.prepare_container()
        logs = signed_container.run_and_get_logs()

        if any([line.endswith('fortanix.com') for line in logs.stdout]):
            return True
        else:
            return False

    def run(self):
        success = True

        for (image, model) in self.legacy_images:
            success = self.run_resigned(input_image=image) and success

        return success
        

if __name__ == '__main__':
    test_app.main(SignerLegacyTest)

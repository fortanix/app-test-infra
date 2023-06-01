#!/usr/bin/python3

import docker
import os
import string_table
import test_app

class TestOpenJ9(test_app.TestApp):
    default_timeout_s = 1200

    def __init__(self, run_args, test_arg_list):
        super(TestOpenJ9, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))
        # Pin image version until ZIRC-3741 is fixed
        image_version='2020051101-59d7e44'
        # Test 1: Basic functional test of openj9. This test case also runs
        # with an 8GB enclave (for SGX), since we have had issues with that
        # working in the past. (Note that the memsize parameter has no
        # effect on the Linux build.)
        container = self.container(image='zapps/openjdk8-openj9',
                                   image_version=image_version,
                                   memsize='8G',
                                   entrypoint=[
                                    '/opt/java/openjdk/bin/java',
                                    '-cp',
                                    '/root',
                                    'HelloWorld'
                                   ],
                                   rw_dirs=['/root'],
                                   java_mode='OPENJ9',
                                   thread_num=1024)
        container.prepare()
        container.copy_file('classes/HelloWorld.class', '/root/');
        logs = container.run_and_return_logs()
        if logs.stdout == ['Hello, World']:
            self.result('test1', 'PASSED')
        else:
            self.result('test1', 'FAILED', 'did not find Hello World output')

        common_options = {
            'java_mode': 'OPENJ9',
            'thread_num': 1024,
            'memsize': '2G',
        }

        # Test 2: Test that JIT is enabled when we run the zircon-friendly openj9
        container = self.container(image='zapps/openjdk8-openj9',
                                   image_version=image_version,
                                   entrypoint=[
                                    '/opt/java/openjdk/bin/java',
                                    '-version',
                                   ],
                                   run_args=[

                                   ],
                                   **common_options)
        container.prepare()
        logs = container.run_and_return_logs()
        if any([line.endswith('(JIT enabled, AOT enabled)') for line in logs.stderr]):
            self.result('test2', 'PASSED')
        else:
            self.result('test2', 'FAILED', 'did not find the expected JIT/AOT state')

        # Test 3: Test that JIT is *not* enabled when we run standard openj9
        container = self.container(image='openjdk8-openj9', registry='adoptopenjdk',
                                   image_version='jdk8u212-b03_openj9-0.14.0',
                                   entrypoint=[
                                    '/opt/java/openjdk/bin/java',
                                    '-version',
                                   ],
                                   **common_options)
        container.prepare()
        logs = container.run_and_return_logs()
        if any([line.endswith('(JIT disabled, AOT disabled)') for line in logs.stderr]):
            self.result('test3', 'PASSED')
        else:
            self.result('test3', 'FAILED', 'did not find the expected JIT/AOT state')

        # Test 4: Test that we can convert a container with no labels.
        # Regression test for ZIRC-2633.
        container = self.container(test_app.BASE_UBUNTU_CONTAINER, registry='library',
                                   image_version=test_app.BASE_UBUNTU_VERSION,
                                   entrypoint=[
                                    '/usr/bin/env',
                                   ],
                                   **common_options)
        container.prepare()

        docker_client = docker.from_env()
        image = docker_client.images.get('{}:{}'.format(test_app.BASE_UBUNTU_CONTAINER, test_app.BASE_UBUNTU_VERSION))
        if image.attrs['Config']['Labels'] is not None:
            self.result('test4', 'FAILED', 'container for this test must not have labels')

        logs = container.run_and_return_logs()
        if 'OPENJ9_JAVA_OPTIONS={}'.format(string_table.JAVA_OPTIONS_OPENJ9_NOJIT) in logs.stdout:
            self.result('test4', 'PASSED')
        else:
            self.result('test4', 'FAILED', 'did not find the expected OPENJ9_JAVA_OPTIONS setting')

        return True

if __name__ == '__main__':
    test_app.main(TestOpenJ9)

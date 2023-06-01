#!/usr/bin/python3

import argparse
import json
import os
import test_app

class TestBash(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestBash, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Bash test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        # Test if we can install a CA cert into the trust store without specifying the caPath
        ca_cert = "-----BEGIN CERTIFICATE-----\nMIIEWDCCAsCgAwIBAgIUD8x9h79Jc8CiYBVPX03BAoPTgp0wDQYJKoZIhvcNAQEL\nBQAwMzExMC8GA1UEAwwoRGF0YXNoaWVsZCBNYXN0ZXIgWm9uZSBFbmNsYXZlIFpv\nbmUgUm9vdDAeFw0xOTEwMjIxNzU1MzVaFw0yNDEwMjExNzU1MzVaMDMxMTAvBgNV\nBAMMKERhdGFzaGllbGQgTWFzdGVyIFpvbmUgRW5jbGF2ZSBab25lIFJvb3QwggGi\nMA0GCSqGSIb3DQEBAQUAA4IBjwAwggGKAoIBgQCw/hSFhXKBzZKd/ounPwGYT4kd\nqdRLgKCO5qn+mJTxt+0CQe9suiYGekht7rMmZ3cAFr32VTsnTHCiMHZifItVBJkW\nb4MTE3ZhaxfXjyg4fUluDJ36JlWL2ShFvHTibvz4QxgQ+5I6OHSJAYzx0OyP0wiG\nb8kU+2tLHcrdyv4Er/XhEEfA8N+yM0etUNHFSAs7JVcsPggfq5xQ5nDgPhvKMGaS\neb+X+AYQqABQ2ZtdxvfnGJh/l0kKNwwD3vFXHQp5JA9giIMzB8NR6MUm3hZlChE0\nqznUeJdsSKNUuut0JoETI0iqkfs8qRVQWsmSZhl+3BErDHMVGpqi1PBpIVEECPKm\nhe+w+/FkgO187WOFcxAXta4IbeDjraJdIpiNvePHcZ/5LBy9oaSVsvrO7O8eHLCm\nccP9d4f+9TSeQw+GKNUuQFYIuRdmcy7n+vFvGsKh53M1LbCVcRSkNDg7ZK4YasOm\nwYgHx/HLtKL84k5UhWdMZSUXrp6RY3NnBUvtfN0CAwEAAaNkMGIwDwYDVR0TAQH/\nBAUwAwEB/zAPBgNVHQ8BAf8EBQMDB4YAMB8GA1UdIwQYMBaAFAo5VHxJaWQZ+j8y\nE3JqGbB1em1zMB0GA1UdDgQWBBQKOVR8SWlkGfo/MhNyahmwdXptczANBgkqhkiG\n9w0BAQsFAAOCAYEACmUmmzE0c3HiLxJVM7o7CszxqTCjZ274mg5XAGBzmTJ7ziSw\nhyRGXVXrRy+8PrfW/dUu9KxBB/fPavq6WjPIUd47D55H6EHW8Q1n5k9K3tJabQKC\nBUG+9LQYfzh7AnHqUupZ+Eo4YC2shiknCMEtNYmmPdyERSmMBwSotRflVGM7hE1z\n/gprL9sXX2OYsUiS+i9MDs3Zud5DYeiQ+PjSnhhNM94TU8VnAbuaY9xPnSqWHiwO\nXeZZ30OwLaQTJsYzlF5S1EdqlkvM7Qyvsuu/Gfcol0jd/L0XHsamIiMetZr9ONn3\n64sNzcMr1W+ue5Q0n7dAsHPADQg8z4MmECGGtVmEA7MjN7Z0k4sncgiYIUjtjwdS\nxbU2wkSzyg6+UmjNbjqy920RJGMs+iGHw9J2Y4YB2stU6PyiIM7BRTB0wFWYhAzl\n2tXtGfqYJIGzfWOUm0lIZtWL/Yx/sj/ji1EOkE4o/FcvD1XAE9Pkg6cFBlmlG6gv\nqys3x7I4n7N4MG8k\n-----END CERTIFICATE-----\n"
        ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : '/etc/ca-certificates.crt',
                "caCert" : ca_cert,
                "system" : 'undefined'
            }
        ]})

        container_args = { 'memsize':'128M', 'nitro_memsize':'2G',
                           'container_env': ['ENCLAVEOS_DEBUG=debug', 'PLATFORM=nitro'] }

        for version in [test_app.BASE_UBUNTU_VERSION, 'bionic-20180821']:
            container = self.container(test_app.BASE_UBUNTU_CONTAINER, registry='library',
                                       image_version=version, entrypoint=['/root/test1.sh'],
                                       ca_certificates=ca_cert_info, **container_args)
            container.copy_to_input_image(['test1.sh', 'test2.sh', 'test5.sh' ], '/root/')
            container.prepare()
            if container.run_and_compare_stdout(['test1 passed']):
                # It would be better if run_and_compare_stdout did this, and logged the output
                self.result('test1-{}'.format(version), 'PASSED')
            else:
                self.result('test1-{}'.format(version), 'FAILED')

        container = self.container(test_app.BASE_UBUNTU_CONTAINER, registry='library',
                                   image_version=test_app.BASE_UBUNTU_VERSION,
                                   entrypoint=['/root/test3.sh'], **container_args)
        container.copy_to_input_image(['test3.sh'], '/root/')
        container.prepare()
        if container.run_and_compare_stdout(['Printed to /dev/stdout', 'test3 passed']):
            self.result('test3', 'PASSED')
        else:
            self.result('test3', 'FAILED')

        # ZIRC-5522: Environment Variable Test
        #   (some variables were set in zircon-apps repo for zapps/ubuntu).
        container = self.container("zapps/ubuntu", image_version='2023010213-523d2ea',
                                    entrypoint=['/root/test6.py'], **container_args)
        container.copy_to_input_image(['test6.py' ], '/root/')
        container.prepare()
        if container.run_and_compare_stdout(['test6 passed']):
            self.result('test6', 'PASSED')
        else:
            self.result('test6', 'FAILED')

        # Test case for ZIRC-5494. This test cases exercises
        # a path where the grep command uses the splice system call.
        # This requires that grep be invoked in a particular way, and requires
        # at least an ubuntu 20 environment. Presumably older versions of
        # grep didn't use splice.
        container = self.container('ubuntu', registry='library',
                                   image_version='20.04',
                                   entrypoint=['/root/shell-test-splice.sh'],
                                   network_mode='none',
                                   **container_args)
        container.copy_to_input_image(['shell-test-splice.sh'], '/root/')
        container.prepare()
        if container.run_and_compare_stdout(['shell-test-splice passed']):
          self.result('shell-test-splice', 'PASSED')
        else:
          self.result('shell-test-splice', 'FAILED')

        return True

if __name__ == '__main__':
    test_app.main(TestBash)

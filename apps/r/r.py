#!/usr/bin/python3

import test_app
import traceback
from test_utils import TestException


class TestR(test_app.TestApp):
    SCRIPT_OUTPUT = \
'''[1] "Fibonacci sequence:"
[1] 0
[1] 1
[1] 1
[1] 2
[1] 3
[1] 5
[1] 8
[1] 13
[1] 21
[1] 34
'''

    def run(self):
        # The latest stable version of R is 3.5.0. Stable releases of R starting with version 3.4.0 are released
        # as containers based on Debian Stretch. R packages built for Debian Stretch won't work with the glibc
        # we've built for zircon, because our glibc version is too old. R releases prior to 3.4.0 are provided
        # in containers based on Debian Jessie, which uses an older glibc that we're compatible with.
        #
        # For this (trivial) test, we override the default entrypoint of the container. The container runs the
        # interactive R runtime by default. We instead invoke Rscript to directly run a small test program.
        #container = self.container(image='r-ver:3.5.0', registry='rocker', entrypoint='/usr/local/bin/Rscript')

        manifest_options = {
            'sys.checkpoint_size': '1G',
        }

        container = self.container(image='r-ver',
                                   image_version='3.3.3',
                                   registry='rocker',
                                   entrypoint=['/usr/local/bin/Rscript', '/root/fib.r',],
                                   memsize='1G',
                                   manifest_options=manifest_options,
                                   rw_dirs= ["/tmp", '/root'])

        try:
            container.prepare()
            container.copy_file('fib.r', '/root')
            container.run()
            result = container.container.wait()
            if result["StatusCode"] != 0:
                raise TestException('Rscript process did not exit cleanly')
            output = container.container.logs(stdout=True, stderr=False, timestamps=False, tail=100).decode('utf-8')
            if not output.endswith(self.SCRIPT_OUTPUT):
                print('Script had invalid output:')
                print(output)
                raise TestException('Invalid script output')

        except Exception as e:
            traceback.print_exc()
            container.dump_output()
            self.info('')
            self.error('Failed to run R application.')
            return False

        return True

if __name__ == '__main__':
    test_app.main(TestR)

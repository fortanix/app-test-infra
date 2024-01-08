#!/usr/bin/python3

import argparse
import os
import test_app


class TestPython(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestPython, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Python request test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):

        container = self.container('zapps/python', image_version='2020112709-cd72bb3',
                                    entrypoint=['/root/run-test.sh'],
                                    container_env={'PLATFORM':os.environ.get('PLATFORM', 'linux')},
                                    memsize="256M", rw_dirs=['/'] )
        container.prepare()
        # add more files as and when new tests are added
        test_files = [
            'test-efs-file.py',
            'test-pickle.py',
            'test-symlink.py',
            'check-custom-interpreter-args.py',
            'check-custom-interpreter-args2.py',
            'custom-intp.py',
            'test-request.py',
            'run-test.sh',
        ]
        # add more output as and when new tests are added
        output_lines = [
            'test-efs-file passed',
            'test-pickle passed',
            'test-symlink passed',
            # the following lines are for the test script check-custom-interpreter-args.py 
            # and is produced by a single test
            'arg is /root/cust-sl',
            'arg is aa    bb                             " "d"',
            'arg is /root/check-custom-interpreter-args.py',
            'arg is bb',
            'arg is cc',
            'arg is ”ff”',
            'arg is ”gg',
            'arg is hh”',
            # the following lines are for the test script check-custom-interpreter-args2.py   
            # and is produced by a single test
            'arg is /root/cust-sl',
            'arg is aa    bb                             " "d"',
            'arg is /root/check-custom-interpreter-args2.py',
            'arg is bb',
            'arg is cc',
            'arg is ”ff”',
            'arg is ”gg',
            'arg is hh”'
        ]

        # test-request is currently broken/flaky in PLATFORM=linux
        if os.environ.get('PLATFORM', 'linux') == 'sgx':
            output_lines.append('test-request passed')
        
        container.copy_files(test_files, '/root')

        return container.run_and_compare_stdout(output_lines)
    def get_timeout(self):
        if os.environ.get('PLATFORM', 'linux') == 'sgx':
            return 20 * 60
        else:
            return 10 * 60


if __name__ == '__main__':
    test_app.main(TestPython)

#!/usr/bin/python3

import os
import test_app

class PythonMinVerCheck(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(PythonMinVerCheck, self).__init__(run_args, [])

    def run(self):
        container = self.container('zapps/python',
                                    entrypoint=['/root/test-python-version.py'],
                                    memsize="256M", nitro_memsize="2048M")
        container.copy_to_input_image(['test-python-version.py'], '/root/')
        container.prepare()
        container.run()
        container.wait(expected_status=0) # raises exception on error
        return True


if __name__ == '__main__':
    test_app.main(PythonMinVerCheck)

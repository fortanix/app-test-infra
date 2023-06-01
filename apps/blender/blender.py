#!/usr/bin/python3

import os
import test_app

class TestBlender(test_app.TestApp):
    input_file = 'blender_input'
    std_result_file = 'blender_output'
    result_file = 'run_output'
    def __init__(self, run_args, test_arg_list):
        super(TestBlender, self).__init__(run_args, [])

    def run(self):
        os.chdir(os.path.dirname(__file__))

        container = self.container(
            'zapps/blender',
            rw_dirs = ['/media', '/usr/lib'],
            memsize='2048M',
            thread_num=80,
        )
        container.prepare()
        container.run()
        container.wait()
        return True

if __name__ == '__main__':
    test_app.main(TestBlender)

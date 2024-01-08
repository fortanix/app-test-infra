#!/usr/bin/python3

import test_app


class TestWorkdir(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestWorkdir, self).__init__(run_args, [])

    def run(self):
        container = self.container('zapps/workdir', memsize="128M")
        container.prepare()
        logs = container.run_and_return_logs()
        if 'VERSION_ID="20.04"' in logs.stdout:
            return True
        else:
            print(str(logs))
            return False

if __name__ == '__main__':
    test_app.main(TestWorkdir)

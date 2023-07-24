#!/usr/bin/python3

import test_app
import argparse

class TestMultUser(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestMultUser, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Multiple user test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):

        container = self.container('zapps/python', memsize='128M', image_version='2021062211-e3e62bc',
                                   entrypoint=['/bin/ls'], user='zircon-tests')

        container.prepare()

        container.run()
        status = container.container.wait()['StatusCode']

        if (status != 0):
            print("Container returned non zero status : {}".format(status))
            raise

        return True


if __name__ == '__main__':
  test_app.main(TestMultUser)

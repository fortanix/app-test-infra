#!/usr/bin/python3

import test_app

class TestPythonWebServerLocalhost(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestPythonWebServerLocalhost, self).__init__(run_args, [])

    def run(self):
        container = self.container('zapps/python-web-server',
                                   image_version='2022120209-aae7f4b',
                                   memsize="2048M",
                                   cpu_count=2,
                                   allow_docker_push_failure=True,
                                   container_env=["TEST_LOCALHOST=true",
                                                  'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE=true',
                                                  "ENCLAVEOS_DEBUG=debug"])
        container.prepare()
        return container.run_and_compare_stdout(["Established a connection to a python web server!"])


if __name__ == '__main__':
    test_app.main(TestPythonWebServerLocalhost)

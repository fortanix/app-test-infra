#!/usr/bin/python3

import docker
import io
import test_app
import argparse

class TestContainerUser(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestContainerUser, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Container user test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        docker_client = docker.from_env()

        # Test that we can run zircon as a non-root user in the container
        # Test both username and uid specification.
        for user in ['nobody', '65534']:
            name = 'container-user-{}'.format(user)

            dockerfile = io.BytesIO(
                    ('FROM {}:{}\n'.format(test_app.BASE_UBUNTU_CONTAINER, test_app.BASE_UBUNTU_VERSION) +
                     'USER {}\n'.format(user) +
                     'ENTRYPOINT ["/usr/bin/id"]\n').encode('utf-8')
                    )
            image = docker_client.images.build(fileobj=dockerfile, tag=name, rm=True)

            container = self.container(name,
                                       registry='library',
                                       image_version='latest',
                                       memsize='128M',
                                       zircon_debug=True,
                                       log_file_path='stderr')
            container.prepare()
            logs = container.run_and_return_logs()
            # The zircon process runs as user nobody in the container
            # The zircon guest believes that it's running as root
            if (any([line.endswith('running as uid 65534, gid 65534') for line in logs.stderr]) and
                'uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)' in logs.stdout[0]):
                self.result(name, 'PASSED')
            else:
                self.result(name, 'FAILED')

        # Test the case where we don't redirect log output to stderr.
        # This is a regression test for ZIRC-1356, where we would fail
        # to run due to inability to access the log file.
        name = 'container-user-nobody'
        container = self.container(name,
                                   memsize='128M',
                                   registry='library',
                                   image_version='latest')
        container.prepare()
        logs = container.run_and_return_logs()
        # The zircon process runs as user nobody in the container
        # The zircon guest believes that it's running as root
        if 'uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)' in logs.stdout[0]:
            self.result('logperms', 'PASSED')
        else:
            self.result('logperms', 'FAILED')

        return True

if __name__ == '__main__':
    test_app.main(TestContainerUser)

#!/usr/bin/python3

import os
import subprocess
import test_app
from test_utils import is_sgx, random_string, remove_ignore_nonexistent, TestException, TimeoutException
from test_utils import get_locust_version
import time
import traceback

VAULT_PORT = 8200
START_TIMEOUT = 60
if is_sgx:
    START_TIMEOUT *= 3
NUM_HEALTH_CHECKS = 5

locust_log = 'locust.log'

class TestVault(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestVault, self).__init__(run_args, [])

        self.vault_token = random_string(24)
        print('Using vault token "{}"'.format(self.vault_token))

    def get_timeout(self):
        if self.soak:
            return 60 * 60
        else:
            return self.default_timeout_s

    # When run under SGX, vault does not seem to be really ready to start handling requests
    # until some time after the health API starts returning results. So make sure we get
    # multiple responses from the health API in a row before we let the test start running.
    def wait_for_vault(self, container, port):
        self.info('waiting for vault to start')

        start = time.time()
        started = False

        curl_stdout = ''
        successes = 0
        while time.time() - start < START_TIMEOUT:

            try:
                # Status is cached and only updates when you call reload().
                container.container.reload()
                if container.container.status != 'running' and container.container.status != 'created':
                    print('Container status is {}'.format(container.container.status))
                    return False
                curl_stdout = subprocess.check_output(['curl',
                                                       '-sS',
                                                       'http://127.0.0.1:{}/v1/sys/health'.format(port),
                                                       '--connect-timeout', '1'],
                                                      stderr=subprocess.STDOUT)
                successes += 1
                print('health check succeeded {} time(s)'.format(successes))
                if successes >= NUM_HEALTH_CHECKS:
                    started = True
                    break
                time.sleep(1)
            except subprocess.CalledProcessError as e:
                successes = 0
                curl_stdout = e.output
                time.sleep(1)

        if not started:
            with open('curl_output', 'wb') as fh:
                fh.write(curl_stdout)
            self.info('Timed out waiting for vault to start. Last curl output:')
            self.info(curl_stdout)
            raise TimeoutException("Timed out waiting for vault to be ready\n")

        return True

    def run(self):
        os.chdir(os.path.dirname(__file__))

        self.info('Starting vault...', end='')

        remove_ignore_nonexistent(locust_log)

        running = False
        container = None
        max_retries = 1
        retries = 0

        while not running:
            retries += 1
            if retries > max_retries:
                raise TestException('Too many retries starting application container')

            if container:
                container.stop()
            ports = {
                VAULT_PORT: None,
            }
            # This environment variable will be set in both the container environment and
            # the manifest environment, so it should be set for both native and zircon runs.
            container_env = {
                'VAULT_DEV_ROOT_TOKEN_ID': self.vault_token, # used by server
                'VAULT_TOKEN': self.vault_token, # used by command line management tool
                'VAULT_ADDR': 'http://127.0.0.1:{}'.format(VAULT_PORT), # used by command line management tool
                # Skip directory chowns done by the wrapper script to work around ZIRC-3381, ZIRC-3382.
                # On SGX we want this anyway, because the contianer already has the correct file ownership
                # and skipping the checks skips a bunch of forks (which are slow).
                'SKIP_CHOWN': '1',
                # Skip the setcap call in the wrapper script. Vault does this so it can use mlock for pages
                # that contain secret information, so they don't get swapped to disk (where it's easier for
                # an attacker to get them than memory). We skip these for multiple reasons: setcap probably
                # won't work in zircon, mlock for this purpose is irrelevant in a zircon app (since all
                # memory is protected, even when swapped out of EPC), and the additional forks are slow on SGX.
                'SKIP_SETCAP': '1',
            }
            manifest_env = [ '{}={}'.format(key, container_env[key]) for key in container_env.keys() ]

            os.environ['VAULT_DEV_ROOT_TOKEN_ID'] = self.vault_token
            container = self.container('vault', registry='library', image_version='1.4.1',
                                       memsize='2048M', thread_num=130, ports=ports,
                                       rw_dirs=['/home/vault'], container_env=container_env,
                                       manifest_env=manifest_env)
            container.prepare()
            container.run()
            port = container.get_port_mapping(VAULT_PORT)
            running = self.wait_for_vault(container, port)

        # The new container is configured with the secrets engine v2 by default. Rather than change the
        # locustfile to use the v2 interface, reconfigure the vault instance to present the v1 secrets
        # engine.
        (code, output) = container.container.exec_run(['vault', 'secrets', 'disable', 'secret'])
        print('Disable secrets output')
        print('{}'.format(output))
        if code != 0:
            print('Disabling kv engine version 2 failed')
            print('{}'.format(output))
            raise TestException(output)

        (code, output) = container.container.exec_run(['vault', 'secrets', 'enable', '-version=1',
                                                       '-path=secret', 'kv'])
        print('Enable secrets output')
        print('{}'.format(output))
        if code != 0:
            print('Enabling kv engine version 1 failed')
            print('{}'.format(output))
            raise TestException(output)

        self.info('Vault is ready. Starting client workload.')
        time_s = 0
        if self.soak:
            # This takes about 15 minutes to run.
            iters = 600000
            time_s = 13*60 # 13 mins
        else:
            # Shorter default number of iterations for CI/local runs.
            iters = 2000
            time_s = 5

        try:
            locust_version = get_locust_version()
            print('locust_version = ', locust_version)
            subprocess.check_output(['locust',
                                     '--headless',
                                     '--only-summary',
                                     '--locustfile=locustfile.py',
                                     '--users=10',
                                     '--run-time={}s'.format(time_s),
                                     '--spawn-rate=100',
                                     '--loglevel=INFO',
                                     '--logfile={}'.format(locust_log),
                                     '--host=http://127.0.0.1:{}'.format(port)])
            return True
        except subprocess.CalledProcessError as e:
            traceback.print_exc()
            self.error('locust failed with returncode {}'.format(e.returncode))
            self.error('locust output: {}'.format(e.output))
            raise


if __name__ == '__main__':
    test_app.main(TestVault)

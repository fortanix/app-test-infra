#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Top-level runner script for the tests container.
#

import argparse
import base64
import docker
import os
import subprocess
import sys
import traceback

ECR_REGION = 'us-west-1'
ENCLAVEOS_HOME = '/home/zircon-tests'
python_dirs = [
    os.path.join(ENCLAVEOS_HOME, 'tests/tools/app-test-infra/python'),
    os.path.join(ENCLAVEOS_HOME, 'tests/codegen/python'),
    os.path.join(ENCLAVEOS_HOME, 'tests/tools/python'),
]

sys.path.extend(python_dirs)

import run_app_tests


def reconstruct_environment():
    # We need to pick up some environment variables from the original
    # environment. We have to pass these manually because the environment
    # gets cleaned when we use sudo to switch users to run this script
    # as zircon-tests.
    with open('tests-env-vars', 'r') as fh:
        for line in fh.readlines():
            (name, value) = line.strip().split('=', 1)
            os.environ[name] = value

# Run a test with the specified command line. stderr/stdout are not
# redirected, so when this is run in a container, it will go to the
# container stderr/stdout, and can be collected from Docker.
# This function returns True if the test passed (i.e. exited with status 0)
# and False if the test failed.
def run_test(test_name, cmdline):
    print('Running test {} with command line "{}"'.format(test_name,
                                                          ' '.join(cmdline)),
          flush=True)
    try:
        subprocess.check_call(cmdline, shell=False)
    except Exception as e:
        traceback.print_exc()
        print('Running test {} failed'.format(test_name))
        return False
    finally:
        print('Ran test {}'.format(test_name))

    return True

def set_env_vars():
    os.environ['ENCLAVEOS_HOME'] = '/home/zircon-tests'
    os.environ['PYTHONPATH'] = ':'.join(python_dirs)
    os.environ['TEST_BASE_DIR'] = os.environ['ENCLAVEOS_HOME']+ '/tests'
    if os.environ.get('PLATFORM', 'linux') == 'sgx':
        os.environ['SGX'] = '1'
    os.environ['ZIRCON_TMPDIR'] = '/tmp'
    os.environ['MALBORK_BINARIES_BASE_DIR'] = os.environ['TEST_BASE_DIR'] + '/' + os.environ['MALBORK_BINARIES'] + '/malbork-artifacts'
    os.environ['FEMC_IMAGE_FILE'] = 'test_image_name.txt'
    os.environ['PACKAGE_PATH'] = os.environ['ENCLAVEOS_HOME'] + '/tests/debian/enclave-os_1.20.devel_amd64.deb'
    os.environ['CONVERTER_IMAGE'] = ' '
    os.environ['CONVERTER_FILE'] = 'converter-docker-image-1.20.devel.tar.gz'
    # TODO: There should be a way to get this value from make/defs.make.
    os.environ['DOCKER_REGISTRY'] = '513076507034.dkr.ecr.us-west-1.amazonaws.com'
    os.environ['TESTS_CONTAINER'] = '1'

def run_command(args):
    try:
        print(" ".join(args))
        env = os.environ.copy()
        subprocess.check_call(args, shell=False, env=env)
    except Exception as e:
        traceback.print_exc()
        return False

    return True

def parse_test_info_files():
    simple_test_list = []
    custom_test_list = []
    status = True
    try:
        with open(os.environ['TEST_BASE_DIR']+"/simple-tests-info.csv", "r") as f:
            for x in f.readlines():

                (test_full_name, timeout, frequency) = str(x).rstrip().split(',')
                test_dir = os.path.dirname(test_full_name)
                test_name = os.path.basename(test_full_name)
                simple_test_list.append([test_dir, test_name, timeout, frequency])

        with open(os.environ['TEST_BASE_DIR']+"/custom-tests-info.csv", "r") as f:
            for x in f.readlines():

                (test_full_name, frequency) = str(x).rstrip().split(',')
                test_dir = os.path.dirname(test_full_name)
                test_name = os.path.basename(test_full_name)
                if os.environ['PLATFORM']=='sgx' and  test_name == 'coredump.py':
                    continue
                custom_test_list.append([test_dir, test_name, frequency])
    except FileNotFoundError:
        return [], [], True
    except Exception as e:
        traceback.print_exc()
        return None, None, False

    return simple_test_list, custom_test_list, True

def run_simple_tests(test_dir, test_bin_name, timeout):
    enclave_os_runner_loc = '/opt/fortanix/enclave-os/bin/enclaveos-runner'
    test_subdir = os.environ['TEST_BASE_DIR'] + "/regression-tests/" + test_dir
    simple_test_runner_script = os.environ['TEST_BASE_DIR'] + '/tools/bin/simple_regression.py'

    os.chdir(test_subdir)

    return run_command([simple_test_runner_script,
                        enclave_os_runner_loc, test_bin_name,
                        str(timeout)])

def run_custom_tests(test_dir, test_bin_name):
    enclave_os_runner_loc = '/opt/fortanix/enclave-os/bin/enclaveos-runner'
    test_subdir = os.environ['TEST_BASE_DIR'] + '/regression-tests/' + test_dir
    custom_test_runner_script = test_subdir + '/' + test_bin_name

    os.chdir(test_subdir)

    return run_command([os.path.join('.', os.path.basename(custom_test_runner_script)), enclave_os_runner_loc])

def run_regression_tests(run_frequency='ci', test_list=None, args=None):
    total_tests = 0
    total_simple_tests = 0
    total_custom_tests = 0

    total_passed = 0
    passed_simple_tests = 0
    passed_custom_tests = 0

    total_failed = 0
    failed_simple_tests = 0
    failed_custom_tests = 0

    passed_simple = []
    passed_custom = []

    failed_simple = []
    failed_custom = []

    # running simple regression tests with simple_regression.py
    simple_test_list, custom_test_list, status = parse_test_info_files()
    if not status:
        return False

    final_success = True
    for (test_dir, test_name, timeout, test_frequency) in simple_test_list:
        full_test_name = os.path.join(test_dir, test_name)

        if not run_app_tests.test_enabled(full_test_name, run_frequency, test_frequency, test_list):
            continue

        total_simple_tests += 1
        total_tests += 1

        if run_simple_tests(test_dir, test_name, timeout):
            passed_simple_tests += 1
            total_passed += 1
            passed_simple.append(full_test_name)
        else:
            failed_simple_tests += 1
            total_failed += 1
            failed_simple.append(full_test_name)
            final_success = False

    # running custom regression tests with custom tests runners
    for (test_dir, test_name, test_frequency) in custom_test_list:
        full_test_name = test_dir + '/' + test_name
        if not run_app_tests.test_enabled(full_test_name, run_frequency, test_frequency, test_list):
            continue

        total_custom_tests += 1
        total_tests += 1


        if run_custom_tests(test_dir, test_name):
            passed_custom_tests += 1
            total_passed += 1
            passed_custom.append(full_test_name)
        else:
            failed_custom_tests += 1
            total_failed += 1
            failed_custom.append(full_test_name)
            final_success = False

    (app_passes, app_failures) = run_app_tests.run_app_tests(env=os.environ.copy(), run_frequency=frequency, test_list=test_list,
                                                             args=args)
    final_success = len(app_failures) == 0 and final_success
    total_tests += len(app_passes) + len(app_failures)
    total_passed += len(app_passes)
    total_failed += len(app_failures)

    assert(total_tests == total_passed + total_failed)
    assert(total_passed == passed_simple_tests + passed_custom_tests + len(app_passes))
    assert(total_failed == failed_simple_tests + failed_custom_tests + len(app_failures))

    print('*** TEST STATISTICS *** ')
    print('Total Tests = {}'.format(total_tests))
    print('Total Simple Tests = {}'.format(total_simple_tests))
    print('Total Custom Tests = {}'.format(total_custom_tests))
    print('Total App Tests = {}\n'.format(len(app_passes) + len(app_failures)))
    print('Total Passed = {}'.format(total_passed))
    print('Passed_simple_tests = {}'.format(passed_simple_tests))
    print('Passed Custom Tests = {}'.format(passed_custom_tests))
    print('Passed App tests = {}'.format(len(app_passes)))

    print('Total Failed = {}'.format(total_failed))
    print('Failed_Simple_tests = {}'.format(failed_simple_tests))
    print('Failed Custom Tests = {}'.format(failed_custom_tests))
    print('Failed App tests = {}'.format(len(app_failures)))

    print('Failed Tests\n', failed_simple + failed_custom + app_failures, '\n')
    return final_success

#
# Unit tests are the simplest tests. The unit tests don't need any additional
# arguments and can be run without needing zircon or the zircon runtime. So
# we just put all of the unit tests into a unit test directory, and this
# script runs them all.
#
def run_unit_tests(test_list=None):
    success = True
    start_dir = os.getcwd()
    unit_tests_dir = '/home/zircon-tests/tests/unit-tests'
    os.chdir(unit_tests_dir)

    for (dirpath, _, files) in os.walk('.'):
        for f in files:
            os.chdir(dirpath)
            exec_path = os.path.join('.', f)
            if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
                if test_list is None or exec_path in test_list:
                    if not run_test(f, [exec_path]):
                        success = False
            os.chdir(unit_tests_dir)

    os.chdir(start_dir)
    return success

def parse_args():
    parser = argparse.ArgumentParser(description='Run the zircon tests')
    parser.add_argument('--app-test-sgx2', action='store_true', help='Run app tests with SGX2')
    parser.add_argument('--app-test-salmiac', action='store_true', help='Run app tests with Salmiac')
    parser.add_argument('--frequency', choices=['smoke', 'ci', 'daily', 'weekly'], default='ci', help='Test suite (frequency) to run')
    parser.add_argument('--test', help='Comma-separated list of tests to run' )
    args = parser.parse_args()
    if args.test:
        test_list = args.test.strip().split(',')
    else:
        test_list = None
    return (args, args.frequency, test_list)

def ecr_login():
    import boto3
    try:
        docker_client = docker.from_env()
        aws_config_b64 = os.getenv('AWS_CONFIG', None)
        if aws_config_b64:
            aws_ecr_region = base64.b64decode(aws_config_b64).decode().split('region = ')[-1].strip()
        else:
            aws_ecr_region = ECR_REGION
        print('Obtained aws region as {}'.format(aws_ecr_region))
        ecr_client = boto3.client('ecr', region_name=aws_ecr_region)
        token = ecr_client.get_authorization_token()
        username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry = token['authorizationData'][0]['proxyEndpoint']
        print('Logging in as user {} into registry {}'.format(username, registry))
        status = docker_client.login(username, password, registry=registry)
        print(status)
    except:
        raise Exception("Unable to log into ECR registry")

if __name__ == '__main__':
    (args, frequency, test_list) = parse_args()
    reconstruct_environment()

    # Other tests (application tests, regression tests, and the converter tests)
    # have additional arguments, like the location of the enclave-os runtime,
    # and timeouts. We'll need to include additional metadata in the form of
    # either a file or python scripts to run these tests.
    #
    set_env_vars()

    success = True

    if args.app_test_salmiac:
        ecr_login()
        success = run_regression_tests(run_frequency=frequency, test_list=test_list, args=args)
    else:
        success = run_unit_tests(test_list=test_list) and success
        success = run_regression_tests(run_frequency=frequency, test_list=test_list, args=args) and success

    if not success:
        print('Test run failed. Some tests failed')
        exit(1)

    print('\n\n\nAll tests passed.')
    exit(0)

#!/usr/bin/python3
#
# Top level script to execute app tests
#

import os
import subprocess
import glob


APPTESTS_FILE = '/home/zircon-tests/tests/app-tests-info.csv'
CONVERTER =         '/home/zircon-tests/tests/tools/converter/bin/build_app.py'
SALMIAC_CONVERTER = '/home/zircon-tests/tests/tools/converter/bin/container-converter'
SECURITY_OPT = 'seccomp=unconfined'
KEY = '/home/zircon-tests/keys/enclave-key.pem'
ENCLAVEOS_PKG_DIR = '/home/zircon-tests/tests/debian/'
INSTALLER = 'enclave-os*.deb'
APPTEST_BASEDIR = '/home/zircon-tests/tests/regression-tests/'

def execute_app_test(testname, dirname, installer, env=None, args=None):
    wd = os.getcwd()
    os.chdir(APPTEST_BASEDIR + dirname)
    arg_list = app_test_arg_list(testname, installer, args)

    try:
        subprocess.check_call(arg_list, shell=False, env=env)
        print("Test " + testname + " passed.")
        os.chdir(wd)
        return True
    except Exception as e:
        print("Test " + testname + " failed.")
        return False


def app_test_arg_list(testname, installer, args=None):
    if args.app_test_salmiac:
        return ["./"+testname,
                '--toolserver', SALMIAC_CONVERTER,
                '--container-env', "nitro",
                '--privileged',
                '--no-results-db',
                '--security-opt', SECURITY_OPT,
                ]
    else:
        arg_list = ["./"+testname,
                    '--toolserver', CONVERTER,
                    '--installer', installer,
                    '--security-opt', SECURITY_OPT,
                    '--key', KEY,
                    '--signer', '/opt/fortanix/enclave-os/bin/enclaveos-signer',
                    ]
        if args.app_test_sgx2:
            arg_list.append('--manifest-option=sgx.memory_model=minimal')

        return arg_list

#
# Less frequent runs also include all the tests from the more frequent runs.
# So ci tests include all of the smoke tests, daily tests include all of
# the weekly tests, and so on.
#


frequency_table = [
    'smoke',
    'ci',
    'daily',
    'weekly',
]

def check_frequency(run_frequency, test_frequency):
    try:
        test_index  = frequency_table.index(test_frequency)
    except ValueError:
        print('test had unknown frequency "{}"'.format(test_frequency))
        return False

    try:
        run_index = frequency_table.index(run_frequency)
    except ValueError:
        print('requested frequency "{}" was unknown'.format(run_frequency))
        return False

    return run_index >= test_index

# Test frequency is handled in a slightly weird way by the Makefiles, mostly
# due to the difficulty of doing complex if condition evaluation in the Makefiles.
# Each test is assigned a single "frequency" value. These are "ci", "daily",
# "weekly", or "broken". A test will run if the test's frequency appears in the
# FREQUENCY make variable. When tests get run, the Make variable FREQUENCY is set
# to a list of one or more frequencies, which specify which tests will be run.
# The list is:
# PR jobs: FREQUENCY=ci
# Soak jobs: FREQUENCY=ci daily
# Weekly zircon test job: FREQUENCY=ci daily weekly
#
# Note that if you set FREQUENCY to just "daily", this will NOT automatically
# include the ci tests. It will ONLY run the tests marked as daily. If you want
# to run the CI and daily tests, you must specifically run with both ci and daily
# in FREQUENCY. This is mostly handled for you automatically if you're using the
# test scripts, but can be necesary if you're running tests by hand using the
# Makefiles.
#
# Since it's easier to write the checks we want in Python, in this script we
# will make it so that if the CI tests are requested, we will only run CI.
# When daily tests are requested, we will run daily and CI tests. And when
# weekly tests are requested, we will run weekly, daily and CI tests.
def test_enabled(full_test_name, run_frequency, test_frequency, test_list):
    if test_list is not None and full_test_name not in test_list:
        print('Skipping test {} (not in list of tests to run)'.format(full_test_name))
        return False

    if full_test_name == 'tools/converter/ci.py':
        print('Skipping test {} (does not work in tests container yet)'.format(full_test_name))
        return False

    ret = check_frequency(run_frequency, test_frequency)
    if not ret:
        print('Skipping test {} (disabled by frequency)'.format(full_test_name))
    return ret

#
# This function returns two lists as a tuple. The first list is the list of the names of the tests that passed.
# The second list is the list of the names of the tests that failed.
#
def run_app_tests(env=None, run_frequency="ci", test_list=None, args=None):
    installer = None
    if not args.app_test_salmiac:
        enclaveos_path = glob.glob(ENCLAVEOS_PKG_DIR + INSTALLER)
        if len(enclaveos_path) != 1:
            print("unique enclaveos deb pkg is missing at " + ENCLAVEOS_PKG_DIR + ". Found following:")
            print(os.listdir(enclaveos_path))
            print("Exiting.")
            exit(1)

        installer = enclaveos_path[0]

    print("Starting execution run of app tests..")
    with open(APPTESTS_FILE, 'r') as f:
        lines = f.read().splitlines()

    tests = {}
    for line in lines:
        test, frequency = line.split(',', 1)
        tests[test] = frequency

    passed_tests = []
    failed_tests = []
    print("test list {}".format(test_list))

    for test, frequency in tests.items():
        testname = os.path.basename(test)
        dirname = os.path.dirname(test)
        if test_enabled(test, run_frequency, frequency, test_list):
            print('Running test {} (frequency {}).'.format(test, frequency))
            if execute_app_test(testname, dirname, installer, env=env, args=args):
                passed_tests.append(test)
            else:
                failed_tests.append(test)
        else:
            print('Skipping test {} (frequency {})'.format(test, frequency))

    return (passed_tests, failed_tests)


if __name__ == '__main__':
    status = run_app_tests()
    print("app tests execution done.")
    exit(status)
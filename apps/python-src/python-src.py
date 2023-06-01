#!/usr/bin/python3
#
# Copyright (C) 2018 Fortanix, Inc. All Rights Reserved.
#

import argparse
import docker
import filecmp
import json
import os
from test_app import TestApp, main
from test_utils import TestException
from test_utils import remove_ignore_nonexistent
import time
import string_table
import datetime

class TestPythonSrc(TestApp):
    # We could reduce the run duration by caliberating ut_timeout
    # In a complete linux run, max a passing case took was 51 secs
    python_run_timeout = (15 * 3600)
    # 4 days to allow regression to complete.
    python_sgx_run_timeout = (96 * 3600)


    # We might want to caliberate this, but due to HUNG test cases,
    # This directly affects the overall run time.
    sgx_tmo_multiplier = 3
    base_ut_timeout = 60
    # TODO caliberate this
    base_suite_timeout = 300
    sgx = 0

    def __init__(self, run_args, test_arg_list):
        super(TestPythonSrc, self).__init__(run_args, [])
        if 'SGX' in os.environ and os.environ['SGX'] == '1':
            self.sgx = 1
        else:
            self.sgx = 0

    def make_predefs(self):
        print("Making predefs")
        predefs_name = './predefs.py'
        try:
          os.remove(predefs_name)
        except OSError:
          pass

        if (self.sgx == 1):
            ut_timeout = self.base_ut_timeout * self.sgx_tmo_multiplier
            suite_timeout = self.base_suite_timeout * self.sgx_tmo_multiplier
        else:
            ut_timeout = self.base_ut_timeout
            suite_timeout = self.base_suite_timeout

        log_file = os.path.join(string_table.INSTALL_LOG_DIR, string_table.ZIRCON_LOG_FILE)
        runner_path = os.path.join(string_table.INSTALL_BIN_DIR, string_table.ZIRCON_EXE_NAME)
        manifest_path=os.path.join(string_table.INSTALL_MANIFESTS_DIR, string_table.CONVERTER_MANIFEST_NAME)

        with open('./predefs.py', 'w') as f:
            f.write("sgx = {}\n".format(self.sgx))
            f.write("log_file = \'{}\'\n".format(log_file))
            f.write("runner_path = \'{}\'\n".format(runner_path))
            f.write("manifest_path = \'{}\'\n".format(manifest_path))
            f.write("timeout_dur = {}\n".format(ut_timeout))
            f.write("suite_timeout_dur = {}\n".format(suite_timeout))




        print("Made predefs")
        return predefs_name

    def run(self):
        ret = False
        os.chdir(os.path.dirname(__file__))
        # This test should not use `latest` as an image version. Do not copy this when adding new app tests.
        post_conv_entry_point=['/cpython/python', '/cpython/run_unit_tests.py']
        container = self.container('zapps/python-test', memsize='2G', image_version='latest',
                                   network_mode='host',
                                   pexpect_tmo=self.get_timeout(),
                                   pexpect=True,
                                   post_conv_entry_point=post_conv_entry_point,
                                   zircon_debug=True)

        try:
            predefs = self.make_predefs();
            container.prepare()
            container.copy_file('./run_unit_tests.py', '/cpython/')
            container.copy_file(predefs, '/cpython/')
            container.copy_file('NON_UT', '/cpython/')
            container.copy_file('suite_list.txt', '/cpython/')
            print("Start time is {}".format(datetime.datetime.now().isoformat()));
            container.run()
            try:
                container.expect('Ran test cases\s*\n')
                ret = True
            except Exception as e:
                print("Run Failed - {}\n".format(e))
        except Exception as e:
            print("Error in running container \n{}\n".format(e));
        finally:
            print("End time is {}".format(datetime.datetime.now().isoformat()));
            if container is not None:
                try:
                    container.copy_dir_from_container('/cpython/python-logs', os.getcwd())
                except Exception as e:
                    # This can happen if the container exits before logs are filled in.
                    print("Unable to copy out python logs - {}\n".format(e))
                    pass
                container.dump_output()

        return ret

    def get_timeout(self):
        if self.sgx:
            return self.python_sgx_run_timeout
        else:
            return self.python_run_timeout


if __name__ == '__main__':
    main(TestPythonSrc)

#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
from enum import Enum
from string_table import (PRODUCT, PRODUCT_VERSION, STARTUP_BANNER_1,
                          STARTUP_BANNER_2)
from test_app import TestApp, main


class TestFlask(TestApp):
    name = 'flask-test'
    image_version = '2020051101-59d7e44'

    class FlaskResult:
        def __init__(self):
            self.output = list()
            self.err = list()
            self.summary = dict()
            self.last_fail = list()

        def fail_contains(self, s):
            if s in self.last_fail:
                return True
            elif s+"," in self.last_fail:
                return True
            else:
                return False

        def print_str(self):
            ret = str()
            if (self.output or self.err):
                ret += "\n===Output:===\n"
                ret += "\t" + "\n\t".join(self.output)
                ret += "\n===Err:===\n"
                ret += "\t" +  "\n\t".join(self.err)
                ret += "\n===Summary:===\n"
                # Better would be to import pprint, that might need a chef update.
                ret += "\t" + "\n\t".join("{}: {}".format(k, v) for k, v in self.summary.items())
                ret += "\n===Failure-list===\n"
                ret += "\t" + "\n\t".join(self.last_fail)
                ret += "\n======\n"
            return ret

    class FlaskErr(Exception):
        class Err(Enum):
            # Error While running the container.
            RUN_ERR_ZIRCON = 1
            RUN_ERR_HOST = 2
            # Unexpected prints on stderr stream of the container.
            STDERR_ZIRCON = 3
            STDERR_HOST = 4
            # Mismatch of summary.
            SUMMARY_ERR = 5

        def __init__(self, err, message):
            self.err = err
            self.message = message
        def __str__(self):
            return self.message

    def __init__(self, run_args, test_arg_list):
        super(TestFlask, self).__init__(run_args, [])
        if 'SGX' in os.environ and os.environ['SGX'] == '1':
            self.sgx = True
        else:
            self.sgx = False

    def container_launch(self, flask_result, err, **kwargs):

        temp_file='temp_last_failed_list'
        try:
            os.remove(temp_file)
        except OSError:
            pass
        flask = self.container('zapps/' + self.name, image_version=self.image_version,
                               memsize='512M', network_mode='host', rw_dirs=['/flask'], **kwargs)
        ret = True
        try:
            flask.prepare()
            flask.run()
            result = flask.container.wait()

            flask_result.output = flask.container\
                     .logs(stdout=True, stderr=False, timestamps=False, tail=100)\
                     .decode('utf-8').rstrip().split('\n')

            flask_result.err = flask.container\
                     .logs(stdout=False, stderr=True, timestamps=False, tail=100)\
                     .decode('utf-8').rstrip().split('\n')

            # Remove ==== at beginning and end
            # Also, summary contains time taken like in 13.2 seconds, which we
            # might not want.
            summary_line = flask_result.output[-1].replace("=", "")\
                    .split("in")[0].strip()

            # Each fragment is of the form `<int> status`,
            # for example `2 failed, 496 passed, 13 skipped`
            summary_fragments = summary_line.split(",")
            for fragment in summary_fragments:
                results = fragment.strip().split()
                flask_result.summary[results[1]] = results[0]
            try:
                flask.copy_file_from_container('/flask/.pytest_cache/v/cache/lastfailed', temp_file)
                with open(temp_file) as f:
                    last_fail = f.read().splitlines()
                    for line in last_fail:
                        flask_result.last_fail.append(line.strip())
            except:
                # If test passes, we would not have a last_fail file.
                pass

        except Exception as e:
            print("Error while running container \n{}\n".format(e));
            flask.dump_output()
            raise(err)
        finally:
            if flask is not None:
                flask.stop()

    # TODO remove after fixing ZIRC-1018 and ZIRC-1522
    def test_workarounds(self, zircon_result, e):
        ret = False
        work_around_zirc_1018 = "\"tests/test_instance_config.py::test_egg_installed_paths\": true"
        work_around_zirc_1522 = "\"tests/test_blueprints.py::test_templates_list\": true"
        if (e.err == self.FlaskErr.Err.SUMMARY_ERR):
            if (zircon_result.summary.get('failed') == '1' and \
                        zircon_result.fail_contains(work_around_zirc_1018)):
                print("Ignoring failure in test_egg_installed_paths")
                ret = True

            if ((zircon_result.summary.get('failed') == '2') and \
                zircon_result.fail_contains(work_around_zirc_1018) and \
                zircon_result.fail_contains(work_around_zirc_1522)):
                print("Ignoring failure in test_egg_installed_paths and test_templates_list")
                ret = True
        return ret


    def run(self):
        ret = True
        os.chdir(os.path.dirname(__file__))

        zircon_result = self.FlaskResult();
        host_result = self.FlaskResult();

        try:
            print("===Running test for {}===\n".format(PRODUCT))
            self.container_launch(zircon_result, self.FlaskErr(self.FlaskErr.Err.RUN_ERR_ZIRCON,
                      "Failed to Run flask container for {}".format(PRODUCT)))

            if zircon_result.err != [''] and \
               zircon_result.err != [STARTUP_BANNER_1 % (PRODUCT_VERSION), STARTUP_BANNER_2]:
                raise self.FlaskErr(self.FlaskErr.Err.STDERR_ZIRCON,
                      "Err while running flask container for {}\n{}"\
                              .format(PRODUCT, zircon_result.err))

            print("===Running test for Host OS===\n")
            self.container_launch(host_result,
                      self.FlaskErr(self.FlaskErr.Err.RUN_ERR_HOST,
                                    "Failed to Run flask container for host os"),
                      post_conv_entry_point="pytest")

            if host_result.err != ['']:
                raise self.FlaskErr(self.FlaskErr.Err.STDERR_HOST,
                        "Err while running flask container for host os\n{}".format(host_result.err))

            # As of now host OS does not have any error, or failures, but
            # some tests do get skipped. We are relying on counts to match
            # here.
            summary_diff = (set(zircon_result.summary) - set(host_result.summary))
            if (summary_diff != set()):
                raise self.FlaskErr(self.FlaskErr.Err.SUMMARY_ERR,
                        "Summaries of host os and {} do not match for {}".format(PRODUCT, summary_diff))

        except self.FlaskErr as e:
            ret = False
            print("===Error===\n\t{}".format(e))
            print("==={} result===\n{}\n".format(PRODUCT, zircon_result.print_str()))
            print("===host os result===\n{}\n".format(host_result.print_str()))
            # TODO remove after fixing ZIRC-1018 and ZIRC-1522
            ret = self.test_workarounds(zircon_result, e)

        return ret



if __name__ == '__main__':
    main(TestFlask)

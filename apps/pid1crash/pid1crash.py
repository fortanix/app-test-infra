#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test for application which crashes with a SIGSEGV in pid1. Regression
# test for ZIRC-4760.


import test_app
import test_utils


class TestPid1Crash(test_app.TestApp):
    def __init__(self, run_args, _):
        super(TestPid1Crash, self).__init__(run_args, [])

    # Check if one or more messages are contained in the specified iterable.
    # messages should be a list of strings to check for. The output will
    # be a list of booleans, indicating for each message whether the message
    # was found or not. For each message, the boolean will be True if the
    # message was found, and False if the message was not found.
    def check_for_messages_in_iterable(self, iterable, messages):
        results = [ False ] * len(messages)

        for line in iterable:
            for i, message in enumerate(messages):
                if message in line:
                    results[i] = True
        return results

    # Same as check_for_messages_in_iterable, except that instead of passing
    # an iterable, directly, this function takes the name of a file to open
    # and check in.
    def check_for_messages_in_log(self, logfile, messages):
        with open(logfile, 'r') as fh:
            return self.check_for_messages_in_iterable(fh, messages)

    def run_testcase(self, testcase):
        # Disable zircon cores. When ZIRC-4760 is present, we treat the crash
        # as a zircon error, and produce a zircon core dump, which is slow.
        manifest_options = {
            'security.coredump.allowed': 'false',
        }
        container = self.container('zapps/pid1crash', image_version='2021071317-8d7773d',
                                   manifest_options=manifest_options,
                                   memsize="128M",
                                   entrypoint=['/root/crash', testcase])
        container.prepare()
        container.run()
        # We know that this container should exit due to the application
        # crashing, so we don't care about the process's exit status.
        # We'll check the enclave-os log to make sure the process exited
        # in the way we were expecting.
        container.wait(ignore_status=True)
        enclaveos_log = container.save_log_file()

        return (enclaveos_log, container.logs())

    def run_segv(self):
        (enclaveos_log, logs) = self.run_testcase('segv')
        # Here we check whether the log contains:
        # 1. The message indicating that the app died from an unhandled signal
        # 2. The message indicating a URTS memory fault
        # 3. The message indicating a zircon internal panic
        #
        # We want message #1 to be present, but not #2 or #3. With bug
        # ZIRC-4760, we were incorrectly treating the guest exception as
        # a URTS memory exception and producing message #2. We really should
        # always produce the zircon internal panic for URTS panics, but
        # we currently don't (ZIRC-4771). There is a function in test_app.py
        # for checking for panics (check_zircon_log_for_panic()), but it's
        # slightly more efficient to check for all three messages at once,
        # and we need to check for the URTS-specific panic message due to
        # ZIRC-4771 right now anyway.
        messages = [
            'Terminating process 1 with unhandled signal',
            'Memory Mapping Exception in Untrusted Code',
            test_utils.zircon_panic_msg,
        ]
        results = self.check_for_messages_in_log(enclaveos_log, messages)

        success = True
        if not results[0]:
            print('Test failed: guest fault message not detected')
            success = False

        if results[1]:
            print('Test failed: URTS memory fault message detected in log')
            success = False

        if results[2]:
            print('Test failed: zircon panic message detected in log')
            success = False

        return success

    def run_hup_urts(self):
        success = True
        (enclaveos_log, logs) = self.run_testcase('hup-urts')
        messages = [ 'Process did not exit after host SIGHUP' ]
        results = self.check_for_messages_in_iterable(logs.stdout, messages)

        if not messages[0]:
            print('Process exited after SIGHUP in URTS')
            success = False

        return success

    def run_hup_ignore(self):
        success = True
        (enclaveos_log, logs) = self.run_testcase('hup-ignore')

        results = self.check_for_messages_in_log(enclaveos_log, ['Terminating process'])
        if results[0]:
            print('sighup-ignore test case failed, process 1 was terminated by signal')
            success = False

        messages = [
            'SIGHUP pending at stage 1',
            'SIGHUP pending at stage 2',
            'SIGHUP not pending at stage 3',
        ]
        results = self.check_for_messages_in_iterable(logs.stdout, messages)
        print('results is {}'.format(results))
        if results != [ True, True, True ]:
            print('sighup-ignore ignored test case failed, SIGHUP not dropped where expected')
            success = False
        
        return success

    def run(self):
        success = True

        success = self.run_segv() and success
        success = self.run_hup_urts() and success
        success = self.run_hup_ignore() and success

        return success

if __name__ == '__main__':
    test_app.main(TestPid1Crash)

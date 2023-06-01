#!/cpython/python
import re
import time
from subprocess import Popen, PIPE
from threading import Timer
import os
import signal
from predefs import *


test_tot = 0
test_passed = 0
test_skipped = 0
test_failed = 0
test_hung = 0
test_broken = 0
test_crashed = 0

timeout = False

logs_dir = os.path.join(os.getcwd(), 'python-logs')
console = os.path.join(logs_dir, 'run-console')
passed = os.path.join(logs_dir, 'PASSED')
failed = os.path.join(logs_dir, 'FAILED')
skipped = os.path.join(logs_dir, 'SKIPPED')
hung = os.path.join(logs_dir, 'HUNG')
crashed = os.path.join(logs_dir, 'CRASHED')
ran = os.path.join(logs_dir, 'RAN')
commands = os.path.join(logs_dir, 'COMMANDS')
counts= os.path.join(logs_dir, 'COUNTS')
debug_logs = log_file

non_ut_list = os.path.join(os.getcwd(), 'NON_UT')
suite_list = os.path.join(os.getcwd(), 'suite_list.txt')
ut_list = os.path.join(os.getcwd(), 'test_list.txt')


def run_pass():
    print("\nRan test cases\n")
    exit(0)

def run_fail(message):
    print("\nRun Failed\n{}\n".format(message))
    exit(-1)

def timeout_hdl(p):
    global timeout
    # We want to kill entir pgid, so that all forks get SIGTERM
    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    timeout = True
    return True

# Not quite tee, as in accepts a single file, also you can't pipe in message.
# We are using it only for printing a few lines (couts of tests)
# So we could afford to open and close the file multiple times.
def tee(file_name, message):
    print(message)
    print("\n")
    try:
        with open(file_name, "a") as f:
            f.write("{}\n".format(message))
    except Exception as e:
        run_fail("Unable to tee {} in {}".format(message, file_name))

def write_console_lines(f, stream):
    for line in stream.strip().decode().splitlines():
        f.write("\t{}\n".format(line))


def log_console(cmd, stdout, stderr):
    try:
        with open(console, "a") as f:
            # Mostly, we won't have Zircon and Python printed in the same line otherwise.
            # This helps us with search patters to land into failure we might want to debug.
            f.write("Zircon Python logs for {} begin\n".format(cmd))

            f.write("Zircon Python stdout for {} begin\n\n".format(cmd))
            write_console_lines(f, stdout)
            f.write("\nZircon Python stdout for {} end\n".format(cmd))

            f.write("Zircon Python stderr for {} begin\n\n".format(cmd))
            write_console_lines(f, stderr)
            f.write("\nZircon Python stderr for {} end\n".format(cmd))

            f.write("Zircon Python debug logs for {} begin\n\n".format(cmd))
            try:
               with open(debug_logs, "r") as fd:
                   for line in fd:
                       f.write("\t{}\n".format(line))
            except:
               pass
            f.write("\nZircon Python debug for {} end\n".format(cmd))
            f.write("Zircon Python logs for {} end\n\n".format(cmd))
    except Exception as e:
        run_fail("Unable to log console for {} in {} - {}".format(cmd, console, e))

def log_status(file_name, cmd, duration = None):
    try:
        with open(file_name, "a") as f:
            f.write("{}".format(cmd))
            if (duration is not None):
                f.write("\t{} s".format(duration))
            f.write("\n")
    except Exception as e:
        run_fail("Unable to log status for {} in {} - {}".format(cmd, file_name, e))


def run(cmd, timeout_sec, ut):

    global test_tot
    global test_passed
    global test_skipped
    global test_failed
    global test_hung
    global test_broken
    global test_crashed
    global timeout

    if ut is True:
        run_cmd = '{} {} -m unittest -v {}'.format(runner_path, manifest_path, cmd)
    else:
        run_cmd = '{} {} -m test -v {}'.format(runner_path, manifest_path, cmd)

    timeout = False
    test_tot = test_tot + 1

    # It might be redudant to list test cases that have ran in the RAN file,
    # when it should match the test_list generated from given Random Seed.
    # But in case the RUN hangs for some reason, we could bash into the
    # container and tail the RAN file to see which is the current script that
    # has executed. 
    # Also, in case of inomplete execution, this would help give us an idea of
    # last list of test case that were actually run till now.
    log_status(ran, cmd)
    log_status(commands, run_cmd)

    # Remove previous stale logs if any.
    try:
        os.remove(debug_logs)
    except OSError:
        pass
    
    # The os.setsid() is passed in the argument preexec_fn so
    # it's run after the fork() and before exec() to run the shell.
    # REF: http://pubs.opengroup.org/onlinepubs/009695399/functions/setsid.html
    # Basically here we give the test case its own pgid,
    # which could be terminated upon timeout.
    proc = Popen(run_cmd, stdout=PIPE, stderr=PIPE, shell=True, preexec_fn=os.setsid)
    time.sleep(0.05)
    tmo_l = lambda : timeout_hdl(proc)
    timer = Timer(timeout_sec, tmo_l)

    log_console_enable = True

    try:
        timer.start()
        ut_start_time = time.time()
        stdout, stderr = proc.communicate()
        ut_end_time = time.time()
        ut_dur = (ut_end_time - ut_start_time)
        stderr_str='{}'.format(stderr)
        stdout_str='{}'.format(stdout)
        if (timeout is True):
            log_status(hung, cmd, ut_dur)
            test_hung = test_hung + 1
        elif (re.match(".*Ran 1 test .*OK (skipped=1)\\n.*", stderr_str) is not None):
            log_status(skipped, cmd, ut_dur)
            test_skipped = test_skipped + 1
        elif (((ut is True) and (re.match(".*Ran 1 test.*OK.*", stderr_str) is not None)) or \
             ((ut is False) and (re.match(".*Tests result:.*SUCCESS.*", stdout_str) is not None))):
            test_passed = test_passed + 1
            log_status(passed, cmd, ut_dur)
            # We might want to skip logging output of passed test cases to reduce log size.
            log_console_enable = False
        elif (((ut is True) and (re.match(".*Ran 1 test.*FAILED.*", stderr_str) is not None)) or \
             ((ut is False) and (re.match(".*Tests result:.*FAILURE.*", stdout_str) is not None))):
            log_status(failed, cmd, ut_dur)
            test_failed = test_failed + 1
        else:
            log_status(crashed, cmd, ut_dur)
            test_crashed = test_crashed + 1
        if (log_console_enable is True):
            log_console(cmd, stdout, stderr)
    except Exception as e:
            print("Exception {}".format(e))
            print("{} broken\n".format(cmd))
            test_broken = test_broken + 1

    finally:
        timer.cancel()


# CI would always run a fresh container
# If we are rerunning the container, it would be better to take out the
# previous logs and remove the folder.
# The script will fail 
def make_logs():
    try:
        os.mkdir(logs_dir)
    except Exception as e:
        run_fail(("Could not create log files - {}.\n"+
                  "Please remove older directory if any\n").format(e))

def print_counts(start, end):
    tee(counts, "Took {} seconds to run all test cases\n".format(end - start))
    tee(counts, "Total {} test cases\n".format(test_tot))
    tee(counts, "Total {} passed\n".format(test_passed))
    tee(counts, "Total {} failed\n".format(test_failed))
    tee(counts, "Total {} skipped\n".format(test_skipped))
    tee(counts, "Total {} hung\n".format(test_hung))
    tee(counts, "Total {} broken\n".format(test_broken))
    tee(counts, "Total {} crashed test case status\n".format(test_crashed))


def run_cases(list_file, skip_set, ut):
    if ut is True:
        timeout_sec = timeout_dur
    else:
        timeout_sec = suite_timeout_dur
    try:
        with open(list_file, 'r') as case_list:
            for case in case_list:
                case = case.rstrip()
                if case in skip_set:
                    continue
                try:
                    run(case, timeout_sec, ut)
                except Exception as e:
                    run_fail("Could not run command {} \n{}".format(case, e))

    except Exception as e:
        run_fail("Could not open file {}\n{}".format(list_file, e))

# Adds strings to a  set containing the names of tests cases.
# This could be used to skip some of the test cases that can't run as UT.
def read_test_set(list_file, test_set):
    with open(list_file, 'r') as fh:
        for line in fh:
            t = line.strip()
            if len(t) == 0:
                continue
            test_set.add(t)





def main():
    make_logs()
    non_ut = set()
    try:
        read_test_set(non_ut_list, non_ut)
    except Exception as e:
        run_fail("Could not open file {} - {}".format(non_ut_list, e))

    start = time.time()
    run_cases(ut_list, non_ut, True)
    run_cases(suite_list, set(), False)
    end = time.time()
    print_counts(start, end)
    if ((test_broken != 0)):
        run_fail("Encountered {} broken tests!".format(test_crashed))
    else:
        run_pass()

if __name__ == "__main__":
    main()

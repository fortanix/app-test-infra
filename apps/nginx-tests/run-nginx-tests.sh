#!/bin/bash -x

#
# Script for running nginx tests. Note that this script deliberately does not
# use -ex, as many of the tests are known to fail under Zircon, and we want
# to run all of the tests even if some tests fail. We post-process the
# container logs to determine if the expected set of tests passed.
#
# The 'skip' file contains a list of tests that we skip running. Some of
# these tests hang under zircon, and some are flaky under zircon.
#
TEST_NGINX_BINARY=/usr/sbin/nginx
export TEST_NGINX_BINARY

TIMEOUT="${TIMEOUT:-60}"

# /home/nginx is actually owned by the root user, but the test runs as nginx.
# So write log files to /tmp instead.
STDOUT_FILE=/tmp/test-runner.stdout
STDERR_FILE=/tmp/test-runner.stderr

rm -f $STDOUT_FILE $STDERR_FILE

for testname in *.t ; do
    # The nginx test scripts have some pretty small timeouts in them that
    # fail regularly on SGX. Unfortunately, there isn't a single wait function
    # that we can hook, so we have a script that changes alarm() and select
    # calls to increase their timeouts.
    if [ "$PLATFORM" == "sgx" ] ; then
        /home/nginx/increase-timeouts.py $testname > /tmp/$testname
        mv -f /tmp/$testname $testname
    fi
    
    # There are a large number of tests that time out, and we need a fairly
    # long timeout for at least some of the tests, so skip tests that are
    # expected to time out to keep the total test time reasonable.
    if ! grep "^$testname$" expected-timeouts.$PLATFORM ; then
        echo -e "\nRunning test $testname" >> $STDOUT_FILE
        echo -e "\nRunning test $testname" >> $STDERR_FILE
        timeout --signal=KILL $TIMEOUT \
                /opt/fortanix/enclave-os/bin/enclaveos-runner \
                /opt/fortanix/enclave-os/manifests/app.manifest.sgx \
                $testname >> $STDOUT_FILE 2>> $STDERR_FILE
        status=$?
        # timeout is supposed to return status 124 if the command timed out, but
        # apparently can also return 137 (= 128 + 9 (SIGKILL)) if requested
        # to send a SIGKILL to the child.
        if [ $status -eq 124 ] || [ $status -eq 137 ]; then
            echo Result: TIMEOUT
        fi
    fi
done

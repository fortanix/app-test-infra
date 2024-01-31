#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Script for rewriting perl expressions in the nginx tests.
#
# The nginx test scripts are written in perl using a test harness called prove.
# Many of the tests have extremely short waits or timeouts (often sub-second)
# that are not long enough when nginx is run under zircon-sgx, but the tests
# can pass reliably when the timeouts are lengthened.
#
# There isn't any central infrastructure in the test scripts controlling how
# long to wait for. So we can't just tweak a slowdown parameter and get the
# test to run. But the majority of the things that check for time in the
# tests use just a handful of different idioms that we can rewrite with a
# script.
#
# Note that the code below does not actually parse the perl syntax, so it is
# not safe to use with arbitrary perl code. We are lucky that these test
# are written in a very uniform way, and we can get away with doing regular
# expression parsing on individual lines. I manually verified that there
# isn't any code in the current nginx tests collection that will cause
# false positives for these regular expressions.
#
# Note that one test file (sub_filter_multi.t) contains binary data embedded
# in the test script that isn't valid unicode. If you try to do the processing
# on strings, Python throws an exception when it can't decode the binary
# data as unicode. To get around this, we read the input file as binary,
# but this forces us to do all the regular expression processing with
# binary strings as well. This is why most of the strings in this file
# are prefixed with b''.

import re
import sys

# This is how much we scale the relevant timeouts by.
scale_timeout = 10

# These tests use select for implementing backend services that nginx
# talks to. We want to increase the run timeout only, but not the select
# timeout. Increasing the select timeout can cause problems by slowing
# down the responses to nginx when it talks to the back-end services.
special_files = [
    'proxy.t',
    'proxy_variables.t',
    'ssi_delayed.t',
    'ssl_stapling.t',
]

def increase_alarm(line):
    # Increase the timeouts for alarms of the form:
    #     alarm(2)
    # don't do anything to alarms like:
    #     alarm(0)
    #
    # alarm(0) cancels any outstanding alarm. Fortunately, any scaling factor
    # times 0 is still 0, so we don't need any special case for 0.
    # The parameter to alarm seems to be an integer, as is the case of the
    # Linux system call.
    match = re.search(b'alarm\((\d+)\)', line)
    if match:
        value = int(match.group(1))
        line = re.sub(b'alarm\(\d+\)',
                      'alarm({})'.format(value * scale_timeout).encode(),
                      line)

    return line

def increase_select(line):
    # This looks for lines matching something like:
    #     select undef, undef, undef, 0.01;
    # but not something like:
    #     select STDERR; $| = 1;
    # In the first expression, the final argument to select (in this case
    # 0.01) is the timeout that we want to scale. The timeout value is
    # in seconds, but the parameter is a floating point value, so sub-second
    # precision is possible.
    match = re.search(b'\s*select\s', line)
    if match:
        args_array = line.split(b',')
        if len(args_array) == 4:
            match = re.search(b'\s*(\d+\.\d+)\s*;', args_array[3])
            if match:
                args_array[3] = re.sub(b'\d+\.\d+',
                                       '{}'.format(float(match.group(1)) *
                                                    scale_timeout).encode(),
                                       args_array[3])
                line = b','.join(args_array) + b'\n'

    return line

def increase_can_read(line):
    # Another form of timeout uses a construction like:
    #     IO::Select->new($s)->can_read(5)
    # or in some cases:
    #     IO::Select->new($s)->can_read($timo || 3)
    # Look for things like that and increase the numeric portion. Like the
    # plain select above, the timeout is in seconds, but can be a floating
    # point value.
    match = re.search(b'can_read\((.*\|\| )?(\d+)\)', line)
    if match:
        new_timeout = float(match.group(2)) * scale_timeout
        line = re.sub(b'can_read\((.*\|\| )?(\d+)\)',
                      'can_read({}{})'.format(str(match.group(1) or ''),
                                              new_timeout).encode(),
                      line)
    return line

def add_run_delay(line):
    # Give the system some time after starting up nginx. Most tests do something
    # like this to start nginx:
    #     my $t = Test::Nginx->new();
    #     $t->run();
    # but some tests do things that are a little more complicated, like
    #     $t->run()->plan(1);
    # or
    #     $t->run()->waitforsocket('127.0.0.1:' . port(8026));
    # It's important that we append to the end of the existing line to work
    # with perl <<EOF construction like this:
    #     my $t = Test::Nginx->new()->has(qw/mail smtp/)->plan(2)
    #             ->write_file_expand('nginx.conf', <<'EOF')->run();
    # The tests seem to assume that the nginx startup time is negligible,
    # which is not true under Zircon. For these cases, when we see a
    # run() somewhere in the line, add a sleep to give us some additional
    # time.
    if b'run()' in line:
        line = line.replace(b'\n', b' sleep(30);\n')

    return line

filename = sys.argv[1]
with open(filename, 'rb') as fh:
    for line in fh:
        if filename not in special_files:
            line = increase_alarm(line)
            line = increase_select(line)
            line = increase_can_read(line)

        line = add_run_delay(line)

        # We have to use sys.stdout.buffer.write() here instead of print,
        # because line contains binary data rather than a (unicode) string.
        sys.stdout.buffer.write(line)
        


#! /bin/bash
# NOTE: The space after the shebang above is an intentional element of this test case.

echo "Output from child process"

# Workaround for ZIRC-144: don't exit while test1.sh is starting the second
# process in the pipeline. We can't use `sleep` because of ZIRC-145.
n=0
while [ $n -lt 1000000 ]; do
    n=$[$n + 1]
done

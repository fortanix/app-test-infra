#!/bin/sh -ex

set -o pipefail

/root/test-efs-file.py
/root/test-pickle.py
/root/test-symlink.py
ln -s /root/custom-intp.py /root/cust-sl
/root/check-custom-interpreter-args.py bb cc ”ff” ”gg hh”

# the following test is similar to the previous one except that the shebang line 
# doesn't end with a new line
/root/check-custom-interpreter-args2.py bb cc ”ff” ”gg hh”
if [ "$PLATFORM" = "sgx" ]; then 
    /root/test-request.py
fi
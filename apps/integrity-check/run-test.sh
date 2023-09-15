#!/bin/sh -ex

# ZIRC-5791
set -o pipefail
tar -cvzf /tmp/opt.tar.gz -C / opt && tar -tvf /tmp/opt.tar.gz

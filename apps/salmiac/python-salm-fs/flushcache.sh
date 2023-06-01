#!/bin/bash -ex

set -o pipefail

if sync && echo 3 > /proc/sys/vm/drop_caches ; then
        echo "Dropped filesystem cache"
        exit 0
else
        echo "Failed to flush filesystem cache"
        exit 1
fi


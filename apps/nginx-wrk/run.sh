#!/bin/bash -ex

set -o pipefail

#
# Usage: run.sh server http_port https_port
#
# This tests the speed of retrieving various static files from a web
# server. The server must be serving both http and https. We exercise
# both for comparison purposes.
#

server=$1
http_port=$2
https_port=$3
duration=$4

rm -rf data
mkdir -p data

CONNECTIONS=${CONNECTIONS:-50}
THREADS=${THREADS:-2}

wrk_params="-c $CONNECTIONS -d $duration -t $THREADS"

function run_wrk {
    wrk $wrk_params "$@" >> output.txt
}

for size in 0 1k 10k 100k ; do
    run_wrk http://$server:$http_port/$size
    run_wrk https://$server:$https_port/$size
done

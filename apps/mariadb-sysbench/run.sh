#!/bin/bash -ex

set -o pipefail

#
# Usage: run.sh 
#
#


password=$1
port=$2
host=$3
duration=$4
db_name=$5
table_size=$6
workload_type=$7

sysbench_params="--test=oltp --mysql-user=root --mysql-password=$password --mysql-port=$port --mysql-host=$host --db-driver=mysql --mysql-db=$db_name --oltp-table-size=$table_size"
function prepare_schema {
    sysbench $sysbench_params "$@"
}

function run_sysbench {
    sysbench $sysbench_params "$@"
}

prepare_schema prepare
for threads in 2 4 8 16; do 
    run_sysbench --max-time=$duration --$workload_type --max-requests=0 --num-threads=$threads run >> output.txt
done

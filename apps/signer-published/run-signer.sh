#!/usr/bin/bash -exu

set -o pipefail

source enclaveos-signer/signer-test
enclaveos-signer/enclaveos-signer "$@"

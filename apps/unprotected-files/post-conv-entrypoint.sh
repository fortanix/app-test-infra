#!/usr/bin/bash

#
# Post conversion entrypoint for the UnprotectedFiles test.
#
# Deletes /.dockerenv and starts the enclave
#

rm /.dockerenv

/opt/fortanix/enclave-os/bin/enclaveos-runner /opt/fortanix/enclave-os/manifests/app.manifest.sgx
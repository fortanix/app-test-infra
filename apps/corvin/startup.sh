#!/bin/bash
echo -e "$1    $2\n" > /etc/hosts
/opt/fortanix/enclave-os/bin/enclaveos-runner /opt/fortanix/enclave-os/manifests/app.manifest.sgx
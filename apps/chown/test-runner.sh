#!/usr/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#
# Post conversion entrypoint for the chown test.
#
# Sets up some unix domain sockets in the host filesystem and then runs
# the test inside of zircon.
#

/usr/bin/nc -l -U /test/sock1 &
/usr/bin/nc -l -U /test/sock2 &

/usr/bin/nc -l -U /efs/sock1 &
/usr/bin/nc -l -U /efs/sock2 &

while [ ! -e /test/sock1 ] || [ ! -e /test/sock2 ] || [ ! -e /efs/sock2 ] ||
          [ ! -e /efs/sock2 ] ;  do
      sleep 1
done

chmod 0777 /test/sock1
chmod 0777 /test/sock2

chmod 0777 /efs/sock1
chmod 0777 /efs/sock2


/opt/fortanix/enclave-os/bin/enclaveos-runner /opt/fortanix/enclave-os/manifests/app.manifest.sgx /test

/opt/fortanix/enclave-os/bin/enclaveos-runner /opt/fortanix/enclave-os/manifests/app.manifest.sgx /efs



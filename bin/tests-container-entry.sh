#!/bin/bash
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Entrypoint script for the tests container.
#
# To have acccess to the docker socket, we need to make the test user able
# to use the docker socket, we have to add a group to the container with
# the same group id as the docker group on the hosts, and add the zircon-tests
# user to that group. Docker really ought to make this easier.
#
# Mostly copied from devops/docker-images-zircon-ci/entry.sh. We don't have
# a way to easily share shell code between devops and zircon.
#
# The AWS config and credentials files for accessing the Fortanix Docker
# registry in AWS should be provided as environment variables. Due
# to docker environment variable file limitations, newlines cannot
# be passed through environment variables. So the contents of these
# environment variables should be base64 encoded.

set -exo pipefail

DOCKER_SOCKET=/var/run/docker.sock
DOCKER_GROUP=docker

function aws_cred_help {
    echo "AWS_CONFIG should contain the base64 encoding of ~/.aws/config"
    echo "AWS_CREDENTIALS should contain the base64 encoding of ~/.aws/credentials"
}

if [ -S ${DOCKER_SOCKET} ]; then
    groupdel $DOCKER_GROUP || true
    DOCKER_GID=$(stat -c '%g' ${DOCKER_SOCKET})
    groupadd -for -g ${DOCKER_GID} ${DOCKER_GROUP}
    usermod -aG ${DOCKER_GROUP} zircon-tests
    if [ -n "$IS_NITRO" ] ; then
      usermod -aG ${DOCKER_GROUP} root
    fi
else
    echo "You need to bind mount Docker socket from host using the flag -v /var/run/docker.sock:/var/run/docker.sock when running the container"
    exit 1
fi

if [ -z "$AWS_CONFIG" ] ; then
    echo "Environment variable AWS_CONFIG was not set"
    aws_cred_help
    exit 1
fi

if [ -z "$AWS_CREDENTIALS" ] ; then
    echo "Environment variable AWS_CREDENTIALS was not set"
    aws_cred_help
    exit 1
fi

mkdir -p /home/zircon-tests/.aws

set +x
echo "$AWS_CONFIG" | base64 -d > /home/zircon-tests/.aws/config
echo "$AWS_CREDENTIALS" | base64 -d > /home/zircon-tests/.aws/credentials

echo "PLATFORM=$PLATFORM" > /home/zircon-tests/tests-env-vars
echo "FLAVOR=$FLAVOR" >> /home/zircon-tests/tests-env-vars
if [ "$PLATFORM" == "sgx" ] ; then
    echo "SGX=1" >> /home/zircon-tests/tests-env-vars
fi
echo "MALBORK_BINARIES=$MALBORK_BINARIES" >> /home/zircon-tests/tests-env-vars

if [ -n "$IS_NITRO" ] ; then
  if [ -z "$ECR_PASSWORD" ] ; then
    echo "Environment variable ECR_PASSWORD was not set"
    exit 1
  fi

  echo "ECR_PASSWORD=$ECR_PASSWORD" >> /home/zircon-tests/tests-env-vars
  echo "AWS_CONFIG=$AWS_CONFIG" >> /home/zircon-tests/tests-env-vars
  echo "AWS_CREDENTIALS=$AWS_CREDENTIALS" >> /home/zircon-tests/tests-env-vars
  echo "FORTANIX_API_KEY=$FORTANIX_API_KEY" >> /home/zircon-tests/tests-env-vars

  # For some reason the default blobs paths is not being used by nitro-cli
  # to fix this we set default path here explicitly.
  echo "NITRO_CLI_BLOBS=/usr/share/nitro_enclaves/blobs/" >> /home/zircon-tests/tests-env-vars

  echo "IS_NITRO=true" >> /home/zircon-tests/tests-env-vars
  sudo losetup
fi
set -x

chown -R zircon-tests:zircon-tests /home/zircon-tests/.aws
usermod -aG root zircon-tests

sudo -u zircon-tests -i \
    /home/zircon-tests/tests/tools/app-test-infra/bin/tests-container-run.py "$@"

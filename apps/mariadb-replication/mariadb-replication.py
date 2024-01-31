#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import json
import os
import pexpect
import random
import string
import test_app
from test_utils import TestException

NUM_TRIALS          = 20
MANAGER_HTTPS_PORT  = 8040
MANAGER_HTTP_PORT   = 8042
DB_PORT             = 3306

# Timeout for each pexpect call.
TEST_PEXPECT_TIMEOUT = 1800

# Overall test timeout
DEFAULT_TIMEOUT = TEST_PEXPECT_TIMEOUT * 10

class TestDBReplication(test_app.TestApp):

    def __init__(self, run_args, test_arg_list):
        # This test is a little special, because it needs multiple containers to run. If you want to run
        # with pre-converted containers, instead of using the --converted-image option, you need to pass
        # additional arguments mariadb master image mariadb slave image mariadb wrong slave image.
        super(TestDBReplication, self).__init__(run_args, [])

        self.converted_images = None
        if len(test_arg_list) > 0:
            if len(test_arg_list) != 3:
                raise ValueError('Run test with test_arg_list mariadb image1(master), mariadb image2 (slave), mariadb image3(wrong slave)')

            self.converted_images = test_arg_list

    def get_timeout(self):
        return DEFAULT_TIMEOUT

    def run(self):
        os.chdir(os.path.dirname(__file__))

        master_name = test_app.gen_hostname('Ftx-db-master')
        slave_name = test_app.gen_hostname('Ftx-db-slave')
        wslave_name = test_app.gen_hostname('Ftx-wslave')
        master_container = None
        slave_container = None
        wslave_container = None

        if self.converted_images:
            assert(len(self.converted_images) == 3)
            converted_master = self.converted_images[0]
            converted_slave = self.converted_images[1]
            converted_wslave = self.converted_images[2]
        else:
            converted_master = None
            converted_slave = None
            converted_wslave = None

        # Start the EM to obtain app certs
        malbork_container = test_app.MalborkContainer()
        malbork_container.start()
        env_malbork=malbork_container.get_env_var()
        os.environ.update(env_malbork)
        node_url = malbork_container.get_node_base_url()

        # Obtain the CA certificate from malbork backend
        ca_cert = malbork_container.get_zone_cert()
        if not ca_cert:
            raise TestException('Unable to get CA cert')

        # __________ MASTER DB container ___________
        self.info('Starting mariadb master...', end='', flush=True)

        # Generate a random root password.
        passwd = ''.join(random.choice(string.ascii_lowercase) for x in range(16))

        repl_user = 'replicator'
        repl_passwd = 'password'

        master_key_file = "/etc/mysql/server-key.pem"
        master_cert_file = "/etc/mysql/server-cert.pem"
        master_ca_file = "/etc/mysql/cacert.pem"

        master_host_env = {
            'NODE_AGENT_BASE_URL'       : node_url,
            'MYSQL_ROOT_PASSWORD'       : passwd,
            'REPLICATION_CERT_SUBJECT'  : slave_name
        }
        master_allow_env = set(master_host_env.keys())
        master_allow_env.remove('NODE_AGENT_BASE_URL')

        master_guest_env = [
            'MYSQL_REPLICATION_MODE=master',
            'MYSQL_REPLICATION_USER={}'.format(repl_user),
            'MYSQL_REPLICATION_PASSWORD={}'.format(repl_passwd),
        ]

        master_cert_info = json.dumps({ "certificates": [
            {
                "issuer"   : "MANAGER_CA",
                "subject"  : master_name,
                "keyType"  : "rsa",
                "keyParam" : { "size": 2048 },
                "keyPath"  : master_key_file,
                "certPath" : master_cert_file,
            }
        ]})

        master_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : master_ca_file,
                "caCert" : ca_cert,
                "system" : "undefined"
            }
        ]})

        master_container = self.container('zapps/mariadb',
                                          converted_image=converted_master,
                                          memsize='2048M', thread_num=80,
                                          encrypted_dirs=['/var/lib/mysql', '/tmp','/run/mysqld'],
                                          rw_dirs=['/var/lib/_mysql', '/etc/mysql'],
                                          network_mode='bridge',
                                          container_env=master_host_env,
                                          manifest_env=master_guest_env,
                                          allow_some_env=master_allow_env,
                                          certificates=master_cert_info,
                                          ca_certificates=master_ca_cert_info,
                                          name=master_name,
                                          pexpect=True,
                                          pexpect_tmo=TEST_PEXPECT_TIMEOUT)
        master_container.prepare()
        master_container.run()

        master_url = 'https://{}:{}'.format(master_container.get_my_ip(), DB_PORT)
        self.info('Mariadb master is running on {}'.format(master_url))

        # Check if the CA certificate was installed in the trust store
        status = master_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not True:
            print("CA cert was not installed in the trust store.")

        try:
            master_container.expect(r'mysqld: Shutdown complete')
            master_container.expect(r'ready for connections')
        except pexpect.ExceptionPexpect as e:
            master_container.dump_output()
            self.info('')
            self.error('Failed to start mariadb master due to exception : {}'.format(e))
            return False

        # __________ SLAVE DB container ___________
        self.info('Starting mariadb slave...', end='', flush=True)

        slave_key_path = "/etc/mysql/server-key.pem"
        slave_cert_path = "/etc/mysql/server-cert.pem"
        slave_ca_path = "/etc/mysql/cacert.pem"

        slave_host_env = {
            'NODE_AGENT_BASE_URL'           : node_url,
            'MYSQL_ROOT_PASSWORD'           : passwd,
            'MYSQL_REPLICATION_MASTER_HOST' : master_name,
        }
        slave_allow_env = set(slave_host_env.keys())
        slave_allow_env.remove('NODE_AGENT_BASE_URL')

        slave_guest_env = [
            'MYSQL_REPLICATION_MODE=slave',
            'MYSQL_REPLICATION_USER={}'.format(repl_user),
            'MYSQL_REPLICATION_PASSWORD={}'.format(repl_passwd),
            'MYSQL_SSL_KEY_PATH={}'.format(slave_key_path),
            'MYSQL_SSL_CERT_PATH={}'.format(slave_cert_path),
            'MYSQL_SSL_CA_PATH={}'.format(slave_ca_path)
        ]

        slave_cert_info = json.dumps({ "certificates": [
            {
                "issuer"   : "MANAGER_CA",
                "subject"  : slave_name,
                "keyType"  : "rsa",
                "keyParam" : { "size": 2048 },
                "keyPath"  : slave_key_path,
                "certPath" : slave_cert_path,
            }
        ]})

        slave_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : slave_ca_path,
                "caCert" : ca_cert,
                "system" : "undefined"
            }
        ]})

        slave_container = self.container('zapps/mariadb',
                                         converted_image=converted_slave,
                                         memsize='2048M', thread_num=80,
                                         encrypted_dirs=['/var/lib/mysql', '/tmp','/run/mysqld'],
                                         rw_dirs=['/var/lib/_mysql', '/etc/mysql'],
                                         network_mode='bridge',
                                         container_env=slave_host_env,
                                         manifest_env=slave_guest_env,
                                         allow_some_env=slave_allow_env,
                                         certificates=slave_cert_info,
                                         ca_certificates=slave_ca_cert_info,
                                         name=slave_name,
                                         pexpect=True,
                                         pexpect_tmo=TEST_PEXPECT_TIMEOUT)
        slave_container.prepare()
        slave_container.run()

        slave_url = 'https://{}:{}'.format(slave_container.get_my_ip(), DB_PORT)
        self.info('Mariadb slave is running on {}'.format(slave_url))

        # Check if the CA certificate was installed in the trust store
        status = slave_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not True:
            print("CA cert was not installed in the trust store.")

        try:
            slave_container.expect(r'mysqld: Shutdown complete')
            slave_container.expect(r'ready for connections')
        except pexpect.ExceptionPexpect as e:
            slave_container.dump_output()
            self.info('')
            self.error('Failed to start mariadb slave due to {}'.format(e))
            return False

        try:
            slave_container.expect(r'Slave I/O thread: connected to master')
        except pexpect.ExceptionPexpect as e:
            slave_container.dump_output()
            self.info('')
            self.info('Slave could not connect to master due to exception : {}'.format(e))
            return False

        slave_container.stop()

        # __________ SLAVE DB container with wrong configuration ___________
        # (The hostname will not match REPLICATION_CERT_SUBJECT passed to master)
        self.info('Starting mariadb slave with wrong config...', end='', flush=True)

        wslave_key_path = "/etc/mysql/server-key.pem"
        wslave_cert_path = "/etc/mysql/server-cert.pem"
        wslave_ca_path = "/etc/mysql/cacert.pem"

        wslave_host_env = {
            'NODE_AGENT_BASE_URL'           : node_url,
            'MYSQL_ROOT_PASSWORD'           : passwd,
            'MYSQL_REPLICATION_MASTER_HOST' : master_name,
        }
        wslave_allow_env = set(wslave_host_env.keys())
        wslave_allow_env.remove('NODE_AGENT_BASE_URL')

        wslave_guest_env = [
            'MYSQL_REPLICATION_MODE=slave',
            'MYSQL_REPLICATION_USER={}'.format(repl_user),
            'MYSQL_REPLICATION_PASSWORD={}'.format(repl_passwd),
            'MYSQL_SSL_KEY_PATH={}'.format(wslave_key_path),
            'MYSQL_SSL_CERT_PATH={}'.format(wslave_cert_path),
            'MYSQL_SSL_CA_PATH={}'.format(wslave_ca_path)
        ]

        wslave_cert_info = json.dumps({ "certificates": [
            {
                "issuer"   : "MANAGER_CA",
                "subject"  : wslave_name,
                "keyType"  : "rsa",
                "keyParam" : { "size": 2048 },
                "keyPath"  : wslave_key_path,
                "certPath" : wslave_cert_path,
            }
        ]})

        wslave_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : wslave_ca_path,
                "caCert" : ca_cert,
                "system" : "true"
            }
        ]})

        wslave_container = self.container('zapps/mariadb',
                                          converted_image=converted_wslave,
                                          memsize='2048M', thread_num=80,
                                          encrypted_dirs=['/var/lib/mysql', '/tmp','/run/mysqld'],
                                          rw_dirs=['/var/lib/_mysql', '/etc/mysql'],
                                          network_mode='bridge',
                                          container_env=wslave_host_env,
                                          manifest_env=wslave_guest_env,
                                          allow_some_env=wslave_allow_env,
                                          certificates=wslave_cert_info,
                                          ca_certificates=wslave_ca_cert_info,
                                          name=wslave_name,
                                          pexpect=True,
                                          pexpect_tmo=TEST_PEXPECT_TIMEOUT)
        wslave_container.prepare()
        wslave_container.run()

        wslave_url = 'https://{}:{}'.format(wslave_container.get_my_ip(), DB_PORT)
        self.info('Mariadb wrong slave is running on {}'.format(wslave_url))

        # Check if the CA certificate was installed in the trust store
        status = wslave_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not True:
            raise TestException("CA cert was not installed in the trust store.")

        try:
            wslave_container.expect(r'mysqld: Shutdown complete')
            wslave_container.expect(r'ready for connections')
        except pexpect.ExceptionPexpect as e:
            wslave_container.dump_output()
            self.info('')
            self.error('Failed to start mariadb wrong slave due to {}'.format(e))
            return False

        try:
            wslave_container.expect(r'Slave I/O: error connecting to master')
        except pexpect.ExceptionPexpect as e:
            wslave_container.dump_output()
            self.info('')
            self.info('Slave mariadb connected to master, which was not expected, exception : {}'.format(e))
            return False

        return True

if __name__ == '__main__':
    test_app.main(TestDBReplication)

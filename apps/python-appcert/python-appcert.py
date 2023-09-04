#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
# Test using ubuntu container to check if app certs are installed
# in the correct location

import json
import os
import time
from test_app import MalborkContainer, TestApp, main, get_zone_cert_local_malbork, get_ip_address
from test_utils import TestException, is_valid_keysize, check_conv_logs

class TestPythonAppcert(TestApp):

    def __init__(self, run_args, test_arg_list):
        super(TestPythonAppcert, self).__init__(run_args, [])

    def run(self):
        malbork_container = MalborkContainer()
        malbork_container.start()
        env_malbork=malbork_container.get_env_var()
        os.environ.update(env_malbork)
        node_url = malbork_container.get_node_base_url()

        # Obtain the CA certificate from malbork backend
        ca_cert = malbork_container.get_zone_cert()
        if not ca_cert:
            raise TestException('Unable to get CA cert')

        ca_path = "/ftx-efs/ca.crt"
        ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : ca_path,
                "caCert" : ca_cert,
                "system" : 'true'
            }
        ]})

        key_sizes = [555, 1024, 92845, 2048]
        count = 2
        container = None
        for ks in key_sizes:
            cert_info = json.dumps({"certificates": [
                {
                    "issuer": "MANAGER_CA",
                    "subject": "Fortanix-python-app",
                    "keyType": "rsa",
                    "keyParam": { "size": ks },
                    "keyPath": "/ftx-efs/key.pem",
                    "chainPath": "/ftx-efs/cert.pem",
                }
            ]})

            try:
                conv_log_file = 'logs/' + str(count) + '.conv.err'
                count += 1
                container = self.container('python', memsize='512M', image_version='3.9.5',
                        registry='library',  network_mode='bridge',
                        certificates=cert_info,
                        container_env={'NODE_AGENT_BASE_URL':node_url},
                        rw_dirs=['/root'], ca_certificates=ca_cert_info,
                        hostname='Fortanix-python-app',
                        entrypoint=['/root/start.py'])

                container.prepare()
                if (not is_valid_keysize(ks)):
                    raise Exception("Test unexpectedly passed with key size " + str(ks))
            except TestException as eve: #ValueError: Invalid key size
                if (is_valid_keysize(ks)):
                    raise ValueError("Test unexpectedly failed with key size " + str(ks))
                status = check_conv_logs(path=conv_log_file, match_str="ValueError: Invalid key size " + str(ks))
                if (not status):
                    raise Exception("Exception found with incorrect error message")
                pass
            except Exception as e:
                raise Exception('Expected exception not found. Error message = ' + str(e))

        container.copy_file('./start.py', '/root/')
        container.run()
        time.sleep(10)
        container.wait(expected_status=0)
        # Check if the CA certificate was installed in the trust store
        status = container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is False:
            raise TestException("CA cert was not installed in the trust store when system was set to true.")

        return True

if __name__ == '__main__':
    main(TestPythonAppcert)

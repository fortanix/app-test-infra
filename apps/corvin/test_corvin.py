#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


import json
import test_app
from test_app import (EMContainer, MalborkContainer, TestApp, get_ip_address,
                      get_zone_cert_local_malbork, main)
from test_utils import random_string


class TestCorvin(TestApp):

    # json template files stores in tools/app-test-infra/apps/corvin
    build_config_file = 'build.json'
    buildjson_template = "template_build.json"
    app_config_json = 'app.json'
    appjson_template = "template_app.json"
    app_name = 'corvin_e2eflow_'+random_string(10)
    rw_record_path = '/tmp/rw'
    success = True

    def update_config_files(self, container):
        with open(TestCorvin.buildjson_template, "r") as build_f:
            build_data = json.load(build_f)
        build_data['docker_info']['docker_image_sha']   = container.converted_image_attributes['imageSHA']
        build_data['docker_image_sha']                  = container.converted_image_attributes['newImage']
        build_data['mrenclave']                         = container.converted_image_attributes['mrenclave']
        build_data['mrsigner']                          = container.converted_image_attributes['mrsigner']
        build_data['isvprodid']                         = container.converted_image_attributes['isvprodid']
        build_data['isvsvn']                            = container.converted_image_attributes['isvsvn']

        print("[build.json]: "+str(build_data))

        # create /tmp/build.json with updated attributes
        with open(TestCorvin.build_config_file, "w") as build_f:
            json.dump(build_data, build_f)

        with open(TestCorvin.appjson_template, "r") as app_f:
             app_data           = json.load(app_f)
        app_data['isvprodid']   = container.converted_image_attributes['isvprodid']
        app_data['isvsvn']      = container.converted_image_attributes['isvsvn']
        app_data['name']        = TestCorvin.app_name
        print("[app.json]: "+str(app_data))

        # create /tmp/app.json with updated attributes
        with open(TestCorvin.app_config_json, "w") as app_f:
            json.dump(app_data, app_f)

    def __init__(self, run_args, test_arg_list):
        super(TestCorvin, self).__init__(run_args, [])

    def run(self):
        cert_info = json.dumps({"certificates": [
        {
           "issuer": "MANAGER_CA",
           "subject": "Fortanix-nginx-curated-app",
           "keyType": "RSA",
           "keyParam": { "size": 2048 },
           "keyPath": "/opt/fortanix/enclave-os/app-config/rw/key.pem",
           "certPath": "/opt/fortanix/enclave-os/app-config/rw/cert.pem",
        }
        ]})
        manifest_opt = {
            "appconfig.em_hostname": "nodes.localhost",
            "appconfig.skip_server_verify": "true",
            "appconfig.port": 9090
        }
        container = self.container("python", memsize='512M', image_version='3.6-slim',
                    registry='library', entrypoint=['/root/start.py'],network_mode='bridge',
                    certificates=cert_info,manifest_options=manifest_opt,
                    hostname='Fortanix-nginx-curated-app',rw_dirs=['/root'])

        container.copy_to_input_image(['start.py', 'startup.sh'], '/root/')
        container.copy_to_input_image(['rw'], '/root/rw')
        container.prepare_image()
        print('Converted image id is {}'.format(container.converted_image))

        self.update_config_files(container)
        em_container = test_app.EMContainer()
        em_container.start()
        configID = em_container.get_config_id()

        if (configID != ""):
            print("ConfigID = "+ configID)
        else:
            print("couldn't find configID")
            raise

        node_url = em_container.get_node_base_url()
        env_var = {
             'NODE_AGENT_BASE_URL':'{}'.format(node_url),
             'APPCONFIG_ID':'{}'.format(configID)
        }
        temp = "{}    nodes.localhost".format(em_container.container.get_my_ip())
        print(temp)
        container.post_conv_entry_point = "/root/startup.sh {}".format(temp)
        container.container_env = env_var
        container.prepare_container()
        container.run()

        status = container.container.wait()['StatusCode']
        if (status != 0):
            print("Container returned non zero status : {}".format(status))
            return False
        print(container.logs())
        return True

if __name__ == '__main__':
    main(TestCorvin)

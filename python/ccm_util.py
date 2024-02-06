# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Utility functions to access CCM via it's REST API.
# They can be used to access any CCM account, perform
# various operations like app/build creation and
# modification. Extensions can be added to support
# workflows.
import json
import os
import requests
import subprocess
import warnings
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List, Optional

DEFAULT_EOS_CCM_URL="https://ccm.stage.fortanix.com"
DEFAULT_EOS_CCM_USERNAME="qa8@fortanix.com"
DEFAULT_EOS_CCM_PASSWORD=""
DEFAULT_EOS_CCM_ACCOUNT_NAME="salmiac-pr-test"
DEFAULT_EOS_CCM_GROUP_NAME="CCM_DEFAULT"

APPTEST_PYTHON_PATH="/home/zircon-tests/tests/tools/app-test-infra/python/"
APP_JSON_TEMPLATE_FILE="template_app.json"
BUILD_JSON_TEMPLATE_NITRO_FILE="template_nitro_build.json"
BUILD_JSON_TEMPLATE_SGX_FILE="template_sgx_build.json"

APP_JSON_PATH="app.json"
BUILD_JSON_PATH="build.json"

APP_JSON_TEMPLATE_PATH = os.path.join(APPTEST_PYTHON_PATH, APP_JSON_TEMPLATE_FILE)
BUILD_JSON_TEMPLATE_NITRO_PATH = os.path.join(APPTEST_PYTHON_PATH, BUILD_JSON_TEMPLATE_NITRO_FILE)
BUILD_JSON_TEMPLATE_SGX_PATH = os.path.join(APPTEST_PYTHON_PATH, BUILD_JSON_TEMPLATE_SGX_FILE)

def update_app_json(converted_image_attributes, app_name, input_image_name, output_image_name, app_description):
    with open(APP_JSON_TEMPLATE_PATH, "r") as app_f:
        app_data = json.load(app_f)

    app_data['isvprodid'] = getattr(converted_image_attributes, 'isvprodid', 0)
    app_data['isvsvn'] = getattr(converted_image_attributes, 'isvsvn', 0)
    app_data['name'] = app_name
    app_data['input_image_name'] = input_image_name
    app_data['output_image_name'] = output_image_name
    app_data['description'] = app_description
    print("[app.json]: "+str(app_data))

    with open(APP_JSON_PATH, "w") as app_f:
        json.dump(app_data, app_f)

def update_build_json(platform, app_id, app_name, converted_image_attributes):
    if platform == "nitro":
        build_template_json = BUILD_JSON_TEMPLATE_NITRO_PATH
    else:
        build_template_json = BUILD_JSON_TEMPLATE_SGX_PATH

    with open(build_template_json, "r") as build_f:
        build_data = json.load(build_f)
    build_data["app_id"] = app_id
    build_data['app_name'] = app_name
    build_data['docker_info']['docker_image_name'] = "zapps/static"
    if platform == "nitro":
        build_data['docker_info']['docker_image_sha'] = converted_image_attributes['sha']
        build_data['docker_info']['docker_image_name'] = converted_image_attributes['name']
        build_data['attributes']['nitro_enclave']['nitro_enclave'] = converted_image_attributes['config']['measurements']['NitroEnclaves']
    else:
        build_data['docker_info']['docker_image_sha'] = converted_image_attributes['imageSHA']
        build_data['mrenclave'] = converted_image_attributes['mrenclave']
        build_data['mrsigner'] = converted_image_attributes['mrsigner']
        build_data['isvprodid'] = converted_image_attributes['isvprodid']
        build_data['isvsvn'] = converted_image_attributes['isvsvn']
    
    print("[build.json]: "+str(build_data))

    with open(BUILD_JSON_PATH, "w") as build_f:
        json.dump(build_data, build_f)


# The environment variables have the highest priority so that the values
# can easily be overridden at runtime. If not values are passed as
# environment variables or as function parameters then, use default values.
def check_configurable_params(env_name, param, def_value):
    env_value = os.getenv(env_name, None)
    if env_value is not None:
        return env_value
    elif param is not None:
        return param
    else:
        return def_value

class CCM:
    def __init__(
        self,
        server=None,
        username=None,
        password=None,
        account_name=None,
        group_name=None,
        verify=False,
    ):
        # Test if any default parameters need to be overridden by environment variables
        self.server = check_configurable_params('DEFAULT_EOS_CCM_URL', server, DEFAULT_EOS_CCM_URL)
        ccm_username = check_configurable_params('DEFAULT_EOS_CCM_USERNAME', username, DEFAULT_EOS_CCM_USERNAME)
        ccm_password = check_configurable_params('DEFAULT_EOS_CCM_PASSWORD', password, DEFAULT_EOS_CCM_PASSWORD)
        self.account_name = check_configurable_params('DEFAULT_EOS_CCM_ACCOUNT_NAME', account_name, DEFAULT_EOS_CCM_ACCOUNT_NAME)
        self.group_name = check_configurable_params('DEFAULT_EOS_CCM_GROUP_NAME', group_name, DEFAULT_EOS_CCM_GROUP_NAME)

        self.auth = HTTPBasicAuth(ccm_username, ccm_password)
        self.session = requests.Session()

        # This allows us to test with a locally deployed CCM
        # backend. Useful for debugging backend fixes/issues.
        if "localhost" in self.server:
            _output = subprocess.run(
                ["/bin/bash", "get_localhost_cert.sh"], capture_output=True
            )
            self.verify = "server.pem"
        else:
            self.verify = verify

        self.user_id = None
        self.account_id = None
        self.group_id = None
        print('CCM Class Initialization complete.')

    def login(self):
        r = self.session.post(
            f"{self.server}/v1/sys/auth",
            verify=self.verify,
            headers={
                "Content-Type": "application/json",
                "X-CSRF-Header": "true",
            },
            auth=self.auth,
        )
        if r.status_code != 200:
            raise ValueError(r.text)
        session_info = r.json()["session_info"]
        self.user_id = session_info["subject_id"]
        self._init_accounts()
        print('Login complete. Account {} : {} ; Group {} : {} selected',
              self.account_name, self.account_id, self.group_name, self.group_id)

    def _user_request_raw(
        self, method, endpoint, json=None, query=None
    ) -> requests.Response:
        with warnings.catch_warnings():
            # ignore warnings (we allow on login() call so we only see it once)
            warnings.filterwarnings("ignore")
            r = self.session.request(
                method=method,
                url=f"{self.server}{endpoint}",
                verify=self.verify,
                headers={
                    "Content-Type": "application/json",
                    "X-CSRF-Header": "true",
                },
                json=json,
                params=query,
            )
        return r

    def _bad_status(self, r: requests.Response):
        if r.status_code == 403:
            print(f"user_id={self.accounts[self.account_id]}")
        raise ValueError("{}: {}".format(r.status_code, r.text))

    def user_post(self, endpoint, json=None) -> requests.Response:
        self.refresh()
        r = self._user_request_raw("POST", endpoint, json)
        if r.status_code != 200:
            self._bad_status(r)
        return r

    def user_delete(self, endpoint, json=None) -> requests.Response:
        self.refresh()
        r = self._user_request_raw("DELETE", endpoint, json)
        if r.status_code == 200 or r.status_code == 204:
            return r
        else:
            self._bad_status(r)

    def user_get(self, endpoint, json=None, query=None) -> requests.Response:
        self.refresh()
        r = self._user_request_raw("GET", endpoint, json=json, query=query)
        if r.status_code != 200:
            self._bad_status(r)
        return r

    def refresh(self):
        r = self._user_request_raw("POST", "/v1/sys/session/refresh")
        if r.status_code != 200:
            print("{}: {}".format(r.status_code, r.text))
            self.login()
        return r.json()

    def user_patch(self, endpoint, json=None) -> requests.Response:
        self.refresh()
        r = self._user_request_raw("PATCH", endpoint, json)
        if r.status_code == 200 or r.status_code == 204:
            return r
        else:
            self._bad_status(r)

    def version(self) -> str:
        return self._user_request_raw("GET", "/v1/sys/version").json()["version"]

    def user_info(self) -> Any:
        return self.user_get(f"/v1/users/{self.user_id}").json()

    def list_accounts(self):
        return self.user_get("/v1/accounts").json()

    def _init_accounts(self):
        if self.account_id is not None:
            return
        accounts = self.list_accounts()["items"]
        self.accounts = {}
        for acct in accounts:
            self.accounts[acct["acct_id"]] = acct["name"]
            if acct["name"] == self.account_name:
                self.account_id = acct["acct_id"]

    def list_apps(self, name=None):
        query_params = {}
        if name:
            query_params["name"] = name
        return self.user_get("/v1/apps", query=query_params).json()

    def create_app(
        self,
        name,
        allowed_domain: Optional[str] = None,
        find_ok=True,
        delete_first=True
    ) -> str:
        if delete_first or find_ok:
            response = self.list_apps(name)
            if response["metadata"]["filtered_count"] > 0:
                app_id = response["items"][0]["app_id"]
                if find_ok:
                    return app_id
                elif delete_first:
                    self.user_delete(f"/v1/apps/{app_id}")
                    print("delete-recreate app config")
        allowed_domains = []
        if allowed_domain:
            allowed_domains.append(allowed_domain)

        with open(APP_JSON_PATH) as app_f:
            app_json_data = json.load(app_f)

        return self.user_post(
            "/v1/apps",
            json=app_json_data,
        ).json()["app_id"]

    def list_builds(self):
        return self.user_get("/v1/builds").json()["items"]

    def create_build(
        self,
        app_id: str,
        find_ok=True,
        delete_first=True,
        approve=True
    ) -> str:
        if delete_first or find_ok:
            for build in self.list_builds():
                if build["app_id"] == app_id:
                    build_id = build["build_id"]
                    if find_ok:
                        return build_id
                    elif delete_first:
                        self.user_delete(f"/v1/builds/{build_id}")
                    else:
                        assert False, "unreachable"

        with open(BUILD_JSON_PATH) as build_f:
            build_json_data = json.load(build_f)

        build = self.user_post(
            "/v1/builds",
            json=build_json_data,
        ).json()
        build_id = build["build_id"]
        if approve:
            pending_task_id = build["pending_task_id"]
            self.approve_build(pending_task_id)
        return build_id

    def list_tasks(self):
        response = self.user_get("/v1/tasks")
        return response.json()["items"]

    def approve_build(self, task_id: str = None, build_id: str = None):
        if task_id is None:
            assert build_id is not None
            for task in self.list_tasks():
                if task["entity_id"] == build_id:
                    task_id = task["task_id"]
                    break
        self.approve_task(task_id)

    def approve_task(self, task_id: str):
        r = self._user_request_raw(
            "PATCH", f"/v1/tasks/{task_id}", json={"status": "APPROVED"}
        )
        if r.status_code != 200:
            self._bad_status(r)

    def get_app(self, app_id: str) -> Any:
        return self.user_get(f"/v1/apps/{app_id}").json()

    def get_build(self, build_id: str) -> Any:
        return self.user_get(f"/v1/builds/{build_id}").json()

    def select_account(self, acct_id: str=None):
        if acct_id is None:
            acct_id = self.account_id
        r = self.user_post(f"/v1/sys/session/select_account/{acct_id}")
        return r.json()

    def create_app_register_build(self, converted_image_attributes, app_name):
       print('CCM version in use : {}'.format(self.version()))
       self.login()
       self.select_account(self.account_id)
       
       app_description="EOS sample app"
       input_image_name="EOS-Input-Image"
       output_image_name="EOS-Output-Image"
       platform = os.getenv('PLATFORM')

       update_app_json(converted_image_attributes, app_name, input_image_name, output_image_name, platform, app_description)
       app_id = self.create_app(name=app_name, image_name=input_image_name,
                                description=app_description, allowed_domain=None,
                                find_ok=True, delete_first=True)
       
       update_build_json(platform, app_id, app_name, json.loads(converted_image_attributes), output_image_name)
       build_id = self.create_build(app_id=app_id, find_ok=True, delete_first=True, approve=True)

    def cleanup_app(self, app_name):
        self.login()
        self.select_account(self.account_id)
        app_info = self.list_apps(app_name)
        if app_info["metadata"]["filtered_count"] > 0:
            app_id = app_info["items"][0]["app_id"]
            self.user_delete(f"/v1/apps/{app_id}")

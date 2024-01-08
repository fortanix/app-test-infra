#!/usr/local/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
# This   test   application   can   be   used   to   validate  corvin  functionality.
# A static copy  of rw  directory  is  used  to  match  with  the  file  genenerated 
# by  enclaveos   manager  in   /opt/fortanix/enclave-os/app-config/rw/.  Make  sure 
# that static copy of rw directory is copied to the /tmp/ directory of the container.

import filecmp
import json
import os

PORTS_PATH="/opt/fortanix/enclave-os/app-config/rw/"
STATIC_PORT_PATH="/root/rw/"

class JsonDataset:
    def __init__(self, credentials, name):
        self.credentials = credentials
        self.name = name
    
def read_json_datasets(parent_path,port):
    ports = []
    for folder in os.listdir(os.path.join(parent_path,port)):
        subfolder = os.path.join(parent_path, port, folder)
        if os.path.exists(os.path.join(subfolder,"dataset")):
            credentials = json.load(open(os.path.join(subfolder,"dataset","credentials.bin"), "r"))
            ports.append(JsonDataset(credentials, folder))
    return ports

def getDatasetPath(parent_path, port):
    subfolder = ""
    for folder in os.listdir(os.path.join(parent_path,port)):
        subfolder = os.path.join(subfolder,folder)
        if os.path.exists(os.path.join(parent_path,port,subfolder,"dataset")):
            subfolder = os.path.join(subfolder,"dataset")
        return subfolder

def filecmpr(d1,d2,filename):
    files = []
    files.insert(0,filename)
    if((os.path.isdir(d1) != False) and ((os.path.isdir(d2) != False))):
        match, mismatch, errors = filecmp.cmpfiles(d1, d2, files, shallow=False)        
        return(match == files)
    else:
        return False

def main():
    status  = True
    if(filecmpr(PORTS_PATH,STATIC_PORT_PATH,"harmonize.txt") == False):
        print("[Test-1]: harmonize.txt failed")
        status &= False
    else:
        print("[Test-1]: harmonize.txt matched")
    
     # check for app configuration generated
    appcfg_path = os.path.join(PORTS_PATH,"appconfig.json")
    if(os.path.exists(appcfg_path)):
        with open(appcfg_path) as t:
            try:
                parsed = json.load(t)
                print("[Test-2]: app configuration is generated \n")
                print(json.dumps(parsed, indent=4, sort_keys=True))
            except Exception as e:
                status &= False
                print("[Test-2]: Invalid json format: {}".format(e))
    else:
        print("[Test-2]: app configuration not generated")
        status &= False
    
    # check for location.txt in input directory
    subfolder_path = getDatasetPath(PORTS_PATH,"input")
    d1 = os.path.join(PORTS_PATH,"input",subfolder_path)
    d2 = os.path.join(STATIC_PORT_PATH,"input",subfolder_path)

    if(filecmpr(d1,d2,"location.txt") == False):
       print("[Test-3]: input dataset location.txt failed")
       status &= False
    else:
        print("[Test-3]: input dataset location.txt matched")

    # check for location.txt in output directory
    subfolder_path = getDatasetPath(PORTS_PATH,"output")
    d1 = os.path.join(PORTS_PATH,"output",subfolder_path)
    d2 = os.path.join(STATIC_PORT_PATH,"output",subfolder_path)

    if(filecmpr(d1,d2,"location.txt") == False):
       print("[Test-4]: output dataset location.txt failed")
       status &= False
    else:
        print("[Test-4]: output dataset location.txt matched")

    # check for credentials.bin in input directory
    input_datasets = read_json_datasets(PORTS_PATH, "input")
    inp_credential = input_datasets[0].credentials["query_string"]
    tmp_input_datasets = read_json_datasets(STATIC_PORT_PATH, "input")
    tmp_inp_credential = tmp_input_datasets[0].credentials["query_string"]
    if(inp_credential == tmp_inp_credential):
        print("[Test-5]: input dataset credential test passed")
    else:
       print("[Test-5]: input dataset credential test failed")
       status &= False

    # check for credentials.bin in output dataset directory
    output_datasets = read_json_datasets(PORTS_PATH, "output")
    out_credential = output_datasets[0].credentials["query_string"]
    tmp_output_datasets = read_json_datasets(STATIC_PORT_PATH, "output")
    tmp_out_credential = tmp_output_datasets[0].credentials["query_string"]
    if(out_credential == tmp_out_credential):
        print("[Test-6]: output dataset credential test passed")
    else:
       print("[Test-6]: output dataset credential test failed")
       status &= False
    
    # finally printing the status of overall test conducted above
    if(status == True):
        print("[overall-test]: corvin test passed")
    else:
        raise Exception("[overall-test]: corvin test failed")
    
    return status
  
if __name__ == "__main__":
    main()

#!/bin/bash

# finally run the scripts
/emsaas/utils/start.sh --with-node-agent --no-expire /emsaas/scripts/workflow_eos.sh /root/build.json /root/app.json

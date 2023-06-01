FROM 513076507034.dkr.ecr.us-west-1.amazonaws.com/zircon-barbican:20170918-58f7363

RUN apt-get update && apt-get -y install gdb python2.7-dbg && apt-get clean && rm -rf /var/lib/apt/lists

RUN pip install pyrasite

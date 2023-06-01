$(SUBDIR)/app-test := $(notdir $(patsubst %/subdir.make,%,$(lastword $(MAKEFILE_LIST)))).py
$(SUBDIR)/app-test-FREQUENCY := $(ci-linux-daily-sgx)

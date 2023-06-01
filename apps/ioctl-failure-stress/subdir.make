ifeq ($(PLATFORM), sgx)
ifeq ($(FLAVOR), debug)
$(SUBDIR)/app-test := ioctl-failure-stress.py
$(SUBDIR)/app-test-FREQUENCY := smoke
endif
endif

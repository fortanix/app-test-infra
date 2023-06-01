ifeq ($(PLATFORM), sgx)
ifeq ($(FLAVOR), debug)
$(SUBDIR)/app-test := enclave-mmap-fail-stress.py
$(SUBDIR)/app-test-FREQUENCY := smoke
endif
endif

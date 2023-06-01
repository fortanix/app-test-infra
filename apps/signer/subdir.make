# The signer test only makes sense to run on SGX. The linux build doesn't
# require containers to be signed.
ifeq ($(PLATFORM),sgx)
$(SUBDIR)/app-test := signer.py
$(SUBDIR)/app-test-FREQUENCY := ci
endif

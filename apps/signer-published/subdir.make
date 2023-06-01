ifeq ($(PLATFORM),sgx)
$(SUBDIR)/app-test := signer-published.py
$(SUBDIR)/copy-files := run-signer.sh set-up-signer.sh
endif

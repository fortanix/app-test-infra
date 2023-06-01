ifneq (,$(filter $(PLATFORM),sgx sim))

$(SUBDIR)/app-test := size01.py

endif

#
# The ewallet test is special because it needs multiple containers.
#

ifneq (,$(filter $(PLATFORM),sgx sim))

$(SUBDIR)/copy-files := locustfile.py
$(SUBDIR)/app-test := ewallet.py
$(SUBDIR)/app-test-FREQUENCY := daily

endif

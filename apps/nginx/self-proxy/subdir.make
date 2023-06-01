$(SUBDIR)/app-test := self-proxy.py
$(SUBDIR)/copy-files := \
	default.conf
ifneq ($(PLATFORM),nitro)
$(SUBDIR)/app-test-FREQUENCY := broken
endif

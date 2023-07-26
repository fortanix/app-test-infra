$(SUBDIR)/app-test := websphere.py

ifeq ($(PLATFORM),nitro)
$(SUBDIR)/app-test-FREQUENCY := ci
else
$(SUBDIR)/app-test-FREQUENCY := daily
endif

$(SUBDIR)/copy-files := \
	alternate-output.html \
	reference-output.html \
	nitro-output.html \

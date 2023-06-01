$(SUBDIR)/app-test := python-numpy.py

# ZIRC-4962
ifeq ($(PLATFORM),linux)
$(SUBDIR)/app-test-FREQUENCY := broken
else
$(SUBDIR)/app-test-FREQUENCY := broken
endif

$(SUBDIR)/copy-files := \
	expected-failures.$(PLATFORM) \
	expected-errors.$(PLATFORM) \

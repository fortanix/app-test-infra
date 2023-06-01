$(SUBDIR)/app-test := nginx-tests.py

ifeq ($(PLATFORM),linux)
nginx-tests-platform := linux
$(SUBDIR)/app-test-FREQUENCY := broken
else
nginx-tests-platform := sgx
$(SUBDIR)/app-test-FREQUENCY := weekly
endif

$(SUBDIR)/copy-files := \
	expected-failures.$(nginx-tests-platform) \
	expected-flaky.$(nginx-tests-platform) \
	expected-notests.$(nginx-tests-platform) \
	expected-passes.$(nginx-tests-platform) \
	expected-timeouts.$(nginx-tests-platform) \
	increase-timeouts.py \
	run-nginx-tests.sh \

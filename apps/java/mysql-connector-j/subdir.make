$(SUBDIR)/app-test := mysql-connector-j.py
$(SUBDIR)/copy-files := linux-expected-errors \
                        linux-expected-failures \
                        linux-expected-skipped \
                        linux-expected-flaky \
                        sgx-expected-errors \
                        sgx-expected-failures \
                        sgx-expected-skipped \
                        sgx-expected-flaky
# Broken (ZIRC-1717, ZIRC-2035, ZIRC-3517, others). Normally daily.
$(SUBDIR)/app-test-FREQUENCY := broken

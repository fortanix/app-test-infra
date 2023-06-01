$(SUBDIR)/app-test := activemq-artemis.py
$(SUBDIR)/copy-files := jms_failed_expected \
                        jms_skipped_expected
# Test is flaky. ZIRC-3518. Normally daily.
$(SUBDIR)/app-test-FREQUENCY := broken

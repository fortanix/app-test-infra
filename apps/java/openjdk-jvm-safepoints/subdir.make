# Both zircon-linux and zircon-sgx now have incorrect behavior
# for mprotect(PROT_NONE) after a page has been given any
# permissions other than PROT_NONE. This is due to limitations
# in SGX, where it is not possible to change page protection to
# PROT_NONE without losing the page contents. The page contents
# cannot be restored atomically, so we leave the pages mapped
# rather than uncommitting them. ZIRC-4527.
$(SUBDIR)/copy-files := classes/HelloWorld.class benchmarks.jar
$(SUBDIR)/app-test := openjdkjvm.py
$(SUBDIR)/app-test-FREQUENCY := broken
$(SUBDIR)/app-test-TIMEOUT := 600000
$(SUBDIR)/openjdkjvm.py-TIMEOUT := 600000

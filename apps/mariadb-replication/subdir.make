ifeq ($(PLATFORM),sgx)
$(SUBDIR)/app-test := mariadb-replication.py
# ZIRC-5908
$(SUBDIR)/app-test-FREQUENCY := broken
endif

ifeq ($(PLATFORM),sgx)
$(SUBDIR)/app-test := mariadb-replication.py
$(SUBDIR)/app-test-FREQUENCY := daily
endif

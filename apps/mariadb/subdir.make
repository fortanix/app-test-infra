$(SUBDIR)/app-test := mariadb.py
ifneq ($(PLATFORM),nitro)
$(SUBDIR)/app-test-FREQUENCY := smoke
endif

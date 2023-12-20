$(SUBDIR)/app-test := mariadb.py
ifneq ($(PLATFORM),nitro)
# ZIRC-5906
$(SUBDIR)/app-test-FREQUENCY := broken
endif

$(SUBDIR)/copy-files := queries.py \
                        reference_index_file.html \
                        reference_index_file_nitro.html \
                        reference_query_file.html

$(SUBDIR)/app-test := elasticsearch.py
ifeq ($(PLATFORM),nitro)
$(SUBDIR)/app-test-FREQUENCY := ci
else
# ZIRC-4148
$(SUBDIR)/app-test-FREQUENCY := broken
endif


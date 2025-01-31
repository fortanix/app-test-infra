ifeq ($(PLATFORM), sgx)
$(SUBDIR)/app-test := test_corvin.py
$(SUBDIR)/copy-files := \
	rw/appconfig.json \
	rw/cert.pem \
	rw/harmonize.txt \
	rw/input/input-1/dataset/credentials.bin \
	rw/input/input-1/dataset/location.txt \
	rw/key.pem \
	rw/output/output-1/dataset/credentials.bin \
	rw/output/output-1/dataset/location.txt \
	rw/tst.txt \
	start.py \
	start_corvin_server.sh \
	startup.sh \
	template_app.json	\
	template_build.json
# ZIRC-5366
$(SUBDIR)/app-test-FREQUENCY := broken
endif

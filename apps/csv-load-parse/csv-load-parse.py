#!/usr/bin/python3
#
# Copyright (C) 2019 Fortanix, Inc. All Rights Reserved.
#
# csv-load-parse app test - Runs a c program that parses data and performs
# some computation on the data

import os
from test_app import TestApp, main

class TestCsvLoadParse(TestApp):

    native_data_file = 'ntime.log'
    zircon_data_file = 'ztime.log'

    def __init__(self, run_args, test_arg_list):
        super(TestCsvLoadParse, self).__init__(run_args)
        self.memsize = '256M'

    def frequency(self):
        frequency = os.getenv('FREQUENCY', default = 'smoke ci')
        print("DB: FREQUENCY = {}".format(frequency))
        return frequency

    def run(self):
        # TODO: Generate files of varying data sizes. This can be useful when
        # testing on machines with larger epc size
        data_dir = '/rw/csv_files/'
        input_file = '{0}medical_csv_10.csv \
                      {0}medical_csv_100.csv \
                      {0}medical_csv_250.csv \
                      {0}medical_csv_500.csv \
                      {0}medical_csv_1000.csv \
                      {0}medical_csv_5000.csv \
                      '.format(data_dir)
        if 'daily' in self.frequency():
            self.memsize = '2G'
            input_file += ' {0}medical_csv_10k.csv \
                      {0}medical_csv_50k.csv \
                      {0}medical_csv_100k.csv \
                      {0}medical_csv_150k.csv \
                      {0}medical_csv_250k.csv \
                      {0}medical_csv_500k.csv \
                      {0}medical_csv_750k.csv \
                      {0}medical_csv_1M.csv \
                      {0}medical_csv_2M.csv \
                      {0}medical_csv_3M.csv \
                      {0}medical_csv_4M.csv'.format(data_dir)
        ops = '0'
        per_row_ops = '1'
        # Run the test natively first
        post_conv_entry_point = "./entrypoint.sh"
        self.runContainer(input_file, post_conv_entry_point, ops, per_row_ops)

        # Run the test in zircon
        post_conv_entry_point = None
        self.runContainer(input_file, post_conv_entry_point, ops, per_row_ops)

        return self.compareResults()

    def compareResults(self):
        try:
            with open(self.native_data_file, 'r') as f:
                native_data = f.readlines()

            with open(self.zircon_data_file, 'r') as f:
                zircon_data = f.readlines()

            print('Rows    load_time(Native/Zircon)    write_time(Native/Zircon)')

            prefix_len = len('medical_csv_')
            for nline, zline in zip(native_data, zircon_data):
                split_ndata = nline.split('=')
                split_zdata = zline.split('=')
                if (len(split_ndata) != len(split_zdata) and len(split_zdata) != 10):
                    print('Error parsing results')
                    return False

                filename_line = split_ndata[1].split()[0]
                filesize_start = filename_line.find('medical_csv_') + prefix_len
                filesize_end = filename_line.find('.csv')
                rows = filename_line[filesize_start:filesize_end]
                nload_time = float(split_ndata[8].split()[0])
                nwrite_time = float(split_ndata[9].split()[0])
                zload_time = float(split_zdata[8].split()[0])
                zwrite_time = float(split_zdata[9].split()[0])

                print('{}    {}    {}'.format(rows, round(nload_time/zload_time, 4), round(nwrite_time/zwrite_time, 4)))
        except:
            print('An error occurred while parsing results')
            return False
        return True

    def getTimeFromLogs(self, logs):
        if logs and logs.stdout[2]:
            words = logs.stdout[2].split(' ')
            return words[3]
        return None

    def runContainer(self, input_file, post_conv_entry_point, ops, per_row_ops):
        output_file = '/rw/test-time.log'
        # TODO: DISABLE_SORT env variable here refers to the number of times the data is sorted
        # in memory, so we should update the name in the entrypoint script to SORT_COUNT
        container = self.container('zapps/csv-load-parse',
                                    rw_dirs=['/rw'],
                                    memsize=self.memsize,
                                    thread_num=128,
                                    container_env={'INPUT_FILE' : input_file,
                                         'NUM_OPS' : ops,
                                         'NUM_ROW_OPS' : per_row_ops,
                                         'ENC_ALGO' : 'RSA',
                                         'DISABLE_SORT' : '1',
                                         'WRITE_OUT' : '1',
                                         'OUTPUT_FILE' : output_file},
                                    post_conv_entry_point=post_conv_entry_point)
        container.prepare()
        container.run()
        status = container.container.wait()['StatusCode']
        if (status != 0):
            print("Container returned non zero status : {}".format(status))
            raise
        if (post_conv_entry_point is None):
            destfile = self.zircon_data_file
        else:
            destfile = self.native_data_file
        container.copy_file_from_container(output_file, destfile)
        container.container.stop()
        return True


    # Override the get_timeout function to set custom app test timeouts
    def get_timeout(self):
        if os.environ['PLATFORM'] == 'sgx':
            return 3 * 60 * 60 * 1000
        else:
            return 120 * 60

if __name__ == '__main__':
    main(TestCsvLoadParse)

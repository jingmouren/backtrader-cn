# -*- coding: utf-8 -*-
import arctic
import tushare as ts
import datetime as dt
import backtradercn.datas.utils as btu
import logging


class TsHisData(object):
    """
    Download and maintain history data from tushare, and provide other modules with the data.

    Attributes:
        db_addr(string): address of the mongodb.
        lib_name(string): name of library.
        coll_names(array): names(stock ids like '000651' for gree) of collections.

    """

    def __init__(self, db_addr, lib_name, *coll_names):
        self.db_addr = db_addr
        self.lib_name = lib_name
        self.coll_names = coll_names
        self.library = None
        self.unused_cols = ['price_change', 'p_change', 'ma5', 'ma10', 'ma20',
                            'v_ma5', 'v_ma10', 'v_ma20', 'turnover']

    def init_data(self):
        """
        Get the recent 1 year's history data when initiate the library.
        1. Connect to arctic and create the library.
        2. Get the recent 1 year's history data from tushare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """
        store = arctic.Arctic(self.db_addr)
        self.library = store.initialize_library(self.lib_name)
        end = dt.datetime.now()
        delta = dt.timedelta(days=btu.Utils.DAYS_PER_YEAR)
        start = end - delta
        for coll_name in self.coll_names:
            his_data = ts.get_hist_data(code=coll_name, start=dt.datetime.strftime(start, '%Y-%m-%d'),
                                        end=dt.datetime.strftime(end, '%Y-%m-%d'), retry_count=5).sort_index()
            if len(his_data) == 0:
                logging.warning('data of stock %s from tushare when initiation is empty' % coll_name)
                continue

            btu.Utils.strip_unused_cols(his_data, *self.unused_cols)

            self.library.write(coll_name, his_data)

    def download_delta_data(self):
        """
        Get today's data and append it to collection.
        1. Connect to arctic and get the library.
        2. Get today's history data from tushare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """
        store = arctic.Arctic(self.db_addr)
        self.library = store[self.lib_name]
        end = dt.datetime.now()
        start = end
        for coll_name in self.coll_names:
            his_data = ts.get_hist_data(code=coll_name, start=dt.datetime.strftime(start, '%Y-%m-%d'),
                                        end=dt.datetime.strftime(end, '%Y-%m-%d'), retry_count=5)
            if len(his_data) == 0:
                logging.warning('delta data of stock %s from tushare is empty' % coll_name)
                continue

            btu.Utils.strip_unused_cols(his_data, *(self.unused_cols))

            self.library.append(coll_name, his_data)

    def get_data(self, coll_name):
        """
        Get all the data of one collection.
        :param coll_name(string): the name of collection.
        :return: data(DataFrame)
        """
        store = arctic.Arctic(self.db_addr)
        self.library = store[self.lib_name]

        return self.library.read(coll_name).data
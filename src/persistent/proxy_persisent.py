#!/usr/bin/python
# coding: UTF-8

import time
import pymysql
import logging

from abc import ABCMeta, abstractmethod
from src.utils.util_func import ip_2_int, int_2_ip, get_datetime_str, add_double_quotation as adq
from DBUtils.PooledDB import PooledDB

class Presisenter(metaclass=ABCMeta):

    @classmethod
    def __init__(self, config):
        self.config = config
        self.init_logger()
        self.logger.info('at Presisenter:__init__()')

    @classmethod
    def init_logger(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s-%(levelname)s-%(message)s',
            datefmt='%y-%m-%d %H:%M',
            filename='./log.txt',
            filemode='a')
        self.logger = logging.getLogger()

    # @classmethod
    # @abstractmethod

class MysqlPresisenter(Presisenter):

    base_sql = {
        'select' : ' select %s from %s %s %s %s %s %s ',
        'update' : ' update %s set %s %s ',
        'insert' : ' insert into %s (%s) values (%s) ',
        'insert_or_update' : ' insert into %s (%s) values (%s) on duplicate key update %s ',
        'delete' : ' delete from %s %s '
    }

    def __init__(self, config):
        self.host = config['host'][0]
        self.port = config['port'][0]
        self.db = config['db'][0]
        self.user = config['user'][0]
        self.passwd = config['passwd']
        if 'charset' not in config:
            self.charset = 'utf8'
        else:
            self.charset = config['charset']
        self.min_cached = config['conn_pool_mincached']
        self.max_cached = config['conn_pool_maxcached']

        self.conn_pool = PooledDB(creator=pymysql,
                                  mincached=self.min_cached,
                                  maxcached=self.max_cached,
                                  host=self.host,
                                  port=self.port,
                                  user=self.user,
                                  passwd=self.passwd,
                                  db=self.db,
                                  use_unicode=False,
                                  charset=self.charset)

    def get_conn(self):
        print('at MysqlPresisenter.get_conn.', self.host, self.port, self.db, self.user, self.passwd, self.charset)
        return self.conn_pool.connection()

    def select(self, table, columns, join='', condition='', group='', order='', limit=''):

        column_names = []
        result_list = list()

        conn = self.get_conn()
        with conn.cursor() as csr:
            print('at select', self.base_sql['select'] % (columns, table, join, condition, group, order, limit))
            csr.execute(self.base_sql['select'] % (columns, table, join, condition, group, order, limit))
            rows = csr.fetchall()
            for row in rows:
                # print([item.decode(encoding=self.charset) for item in row])
                result_list.append([item.decode(encoding=self.charset) for item in row])

            for line_info in csr.description:
                # print(line_info)
                column_names.append(line_info[0])
        conn.close()
        print('at select', column_names, result_list)
        return column_names, result_list

    def commit(self, sql, arg):
        conn = self.get_conn()
        with conn.cursor() as csr:
            csr.execute(sql % arg)
        conn.commit()
        conn.close()
        return csr.rowcount

    def commit_batch(self, sql, batch_list):

        if len(batch_list) < 1:
            return 0

        conn = self.get_conn()
        with conn.cursor() as csr:
            #print('at MysqlPresisenter.commit_batch after get_conn.')
            for arg in batch_list:
                print('commit_batch', sql % arg)
                csr.execute(sql % arg)
            # csr.executemany(sql, batch_list)
        conn.commit()
        conn.close()
        return csr.rowcount

    def update(self, table, set_value, condition=''):
        return self.commit(self.base_sql['update'], (table, set_value, condition))

    def update_batch(self, batch_list):
        return self.commit_batch(self.base_sql['update'], batch_list)

    def insert(self, table, columns, values):
        return self.commit(self.base_sql['insert'], (table, columns, values))

    def insert_batch(self, batch_list):
        return self.commit_batch(self.base_sql['insert'], batch_list)

    def insert_or_update(self, table, columns, values, duplicate_update):
        return self.commit(self.base_sql['insert_or_update'], (table, columns, values, duplicate_update))

    def insert_or_update_batch(self, batch_list):
        return self.commit_batch(self.base_sql['insert_or_update'], batch_list)

    def delete(self, table, condition):
        return self.commit(self.base_sql['delete'], (table, condition))

class ProxyPresisenter(object):

    select_column_str = ' ip, port, p_type '

    update_active_set_str = ' resp_time = %s, ' \
                            'speed = %s, ' \
                            'valid_times = valid_times + 1, ' \
                            'is_active = 1, ' \
                            'update_time = %s '

    update_inactive_set_str = ' resp_time = 0, ' \
                              'speed = 0, ' \
                              'invalid_times = invalid_times + 1, ' \
                              'is_active = 0 '

    update_condition_str = ' where num_ip = %s and p_type = %s and port = %s '

    insert_columns_str = ' num_ip, p_type, port, ip, resp_time, speed, valid_times '

    insert_duplicate_update_str = ' resp_time = %s, ' \
                                  'speed = %s, ' \
                                  'valid_times = valid_times + 1, ' \
                                  'is_active = 1, ' \
                                  'update_time = %s '

    def init_config(self, config):
        # print(config)
        self.config = config
        self.storage_config = config['storage_config']
        self.storage = MysqlPresisenter(self.storage_config)
        self.batch_size = config['batch_size']
        self.input_queue = config['input_queue']
        self.output_queue = config['output_queue']
        self.table_name = config['table_name']
        self.sleep_interval = config['sleep_interval']
        self.active_update_seconds = config['active_update_seconds']
        self.inactive_update_seconds = config['inactive_update_seconds']
        self.inactive_del_seconds = config['inactive_del_seconds']

    def run(self, config):

        self.init_config(config)

        print('at ProxyPresisenter.run before while True.')

        self.send_active_proxy()
        self.send_inactive_proxy()

        active_last_time = time.time()
        inactive_last_time = time.time()

        try:
            while True:

                print('at ProxyPresisenter.run after while True.')

                current_active_time = time.time()
                if current_active_time - active_last_time > self.active_update_seconds:
                    print('in ProxyPresisenter.run after if current_active_time - active_last_time.', current_active_time - active_last_time, self.active_update_seconds)
                    active_last_time = current_active_time
                    self.send_active_proxy()
                    self.del_inactive_proxy()
                print('after ProxyPresisenter.run after if current_active_time - active_last_time.', current_active_time - active_last_time, self.active_update_seconds)
                current_inactive_time = time.time()
                if current_inactive_time - inactive_last_time > self.inactive_update_seconds:
                    print('in ProxyPresisenter.run after if current_inactive_time - inactive_last_time.', current_inactive_time - inactive_last_time, self.inactive_update_seconds)
                    inactive_last_time = current_inactive_time
                    self.send_inactive_proxy()

                print('after ProxyPresisenter.run after if current_inactive_time - inactive_last_time.', current_inactive_time - inactive_last_time, self.inactive_update_seconds)
                spider_active, presis_active, presis_inactive = self.handle_queue()

                print('at ProxyPresisenter.run after self.handle_queue().')
                if len(presis_active) > 0 or len(presis_inactive) > 0:
                    self.handle_presisent_proxy(presis_active, presis_inactive)
                print('at ProxyPresisenter.run after self.handle_presisent_proxy().')
                if len(spider_active) > 0:
                    self.handle_spider_proxy(spider_active)
                print('at ProxyPresisenter.run after self.handle_spider_proxy().')

                time.sleep(self.sleep_interval)
        except Exception as e:
            print('at ProxyPresisenter.run:except', str(e))

    def del_inactive_proxy(self):
        self.storage.delete(self.table_name,
                            condition=' where is_active = 0 and now() - update_time > ' + str(self.inactive_del_seconds))

    def send_active_proxy(self):
        column_names, active_list = self.storage.select(self.table_name, self.select_column_str, condition=' where is_active = 1 ')
        print('at ProxyPresisenter.send_active_proxy', column_names, active_list)

        for active_proxy in active_list:
            print('at ProxyPresisenter.send_active_proxy', active_proxy)
            self.output_queue.put(('persisent', active_proxy))

    def send_inactive_proxy(self):
        column_names, inactive_list = self.storage.select(self.table_name, self.select_column_str, condition=' where is_active = 0 ')
        print('at ProxyPresisenter.send_inactive_proxy', column_names, inactive_list)
        for inactive_proxy in inactive_list:
            print('at ProxyPresisenter.send_inactive_proxy', inactive_list)
            self.output_queue.put(('persisent', inactive_proxy))

    def handle_presisent_proxy(self, active_list, inactive_list):

        update_list = []

        for ip, port, p_type, resp_time, speed in active_list:

            update_list.append((self.table_name,
                                self.update_active_set_str % (str(resp_time), str(speed), adq(get_datetime_str())),
                                self.update_condition_str % (str(ip_2_int(ip)), adq(p_type), port)))
        print('at ProxyPresisenter.handle_presisent_proxy after for active_list.', inactive_list)
        for ip, port, p_type, resp_time, speed in inactive_list:

            #print(type(ip), type(port), type(p_type), type(resp_time), type(speed))

            inactive_condition_str = self.update_condition_str % (str(ip_2_int(ip)), adq(p_type), port)

            update_list.append((self.table_name, self.update_inactive_set_str, inactive_condition_str))

        print('at ProxyPresisenter.handle_presisent_proxy after for inactive_list.')
        return self.storage.update_batch(update_list)

    def handle_spider_proxy(self, proxy_list):

        insert_or_update_list = []

        for ip, port, p_type, resp_time, speed in proxy_list:

            print('at ProxyPresisenter.handle_spider_proxy', ip, port, p_type, resp_time, speed)

            insert_or_update_values = ', '.join([str(ip_2_int(ip)), adq(p_type), port, adq(ip), str(resp_time), str(speed), '1'])
            print('at ProxyPresisenter.handle_spider_proxy:insert_or_update_values', insert_or_update_values)
            duplicate_update_str = self.insert_duplicate_update_str % (str(resp_time), str(speed), adq(get_datetime_str()))
            print('at ProxyPresisenter.handle_spider_proxy:duplicate_update_str', duplicate_update_str)

            insert_or_update_list.append((self.table_name,
                                          self.insert_columns_str,
                                          insert_or_update_values,
                                          duplicate_update_str))
            print('at ProxyPresisenter.handle_spider_proxy:insert_or_update_list', insert_or_update_list)
        return self.storage.insert_or_update_batch(insert_or_update_list)

    def handle_queue(self):

        input_queue_size = self.input_queue.qsize()

        spider_active_proxy_list = []
        presisent_active_proxy_list = []
        presisent_inactive_proxy_list = []

        if input_queue_size > 0:

            for i in range(input_queue_size if input_queue_size < self.batch_size else self.batch_size):

                source, proxy_active, proxy_info = self.input_queue.get_nowait()

                if proxy_info is not None:

                    if proxy_active:
                        if source == 'spider':
                            spider_active_proxy_list.append(proxy_info)
                        elif source == 'persisent':
                            presisent_active_proxy_list.append(proxy_info)
                    else:
                        print('at handle_queue', proxy_info)
                        presisent_inactive_proxy_list.append(proxy_info)
        return spider_active_proxy_list, presisent_active_proxy_list, presisent_inactive_proxy_list

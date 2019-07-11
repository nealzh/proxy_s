#!/usr/bin/python
# coding: UTF-8

import re
import time
import pandas as pd
import logging
import requests

from bs4 import BeautifulSoup as bfs
from urllib.parse import urljoin
from src.utils.util_func import gen_sleep_interval_func


class KUAISpider(object):

    def __init__(self):
        pass

    def init_config(self, config):
        self.config = config
        self.start_url = config['start_url']
        self.headers = config['headers']
        self.timeout = config['timeout']
        self.sleep_interval_func = gen_sleep_interval_func(config['sleep_interval_mu_factor'], config['sleep_interval_min'])
        self.input_names = config['input_names']
        self.output_names = config['output_names']
        self.output_queue = config['output_queue']
        self.regx = re.compile('\s+')

        self.init_logger()
        print('at KUAISpider:init_config()')
        self.logger.info('at KUAISpider:init_config()')

    def init_logger(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s-%(levelname)s-%(message)s',
            datefmt='%y-%m-%d %H:%M',
            filename='./log.txt',
            filemode='a')
        self.logger = logging.getLogger()

    def get_pages(self, html):

        page_html = html.find('div', id='listnav')
        a_list = page_html.find_all('a')

        for i in range(len(a_list)):
            a = a_list[i]
            if 'class' in a.attrs:
                if a.attrs['class'][0] == 'active':
                    current_page = self.regx.sub('', a.text)
                    if i < len(a_list) - 1:
                        next_page = a_list[i + 1].attrs['href']
                        break
                    else:
                        next_page = None

        return (current_page, next_page)

    def get_page_data(self, html):

        table = html.find('table', class_='table table-bordered table-striped')
        table_head = []
        for th in table.find_all('th'):
            table_head.append(self.regx.sub('', th.text))
        table_data = []
        for tr in table.find('tbody').find_all('tr'):
            current_col = []
            for td in tr.find_all('td'):
                current_col.append(self.regx.sub('', td.text.lower()))
            table_data.append(current_col)
        return pd.DataFrame(table_data, columns=table_head)

    def replace_table_names(self, table_df, input_names=None, output_names=None):

        if not input_names:
            input_names = self.input_names

        if not output_names:
            output_names = self.output_names

        need_cols = table_df[input_names]
        need_cols.columns = output_names
        return need_cols

    def run(self, config, next_page=True, page_limit=-1, retry_times=3):

        print('at KUAISpider.run before init_config.')

        self.init_config(config)
        print('at KUAISpider.run after init_config.')
        self.logger.info('at KUAISpider.run after init_config.')

        try:
            self.logger.info(self.start_url)

            current_url = self.start_url

            sess = requests.Session()

            page_count = 1

            while next_page:

                sleep_time = self.sleep_interval_func()
                # headers['Referer'] = current_url
                resp = sess.get(current_url, headers=self.headers, timeout=self.timeout)
                html = bfs(resp.text, 'html5lib')

                if resp.status_code == 200 and len(html) > 0:

                    for proxy in self.replace_table_names(self.get_page_data(html)).values.tolist():
                        self.output_queue.put(('spider', proxy))

                    current_page, next_page_url = self.get_pages(html)

                    if (page_limit == -1 or page_count < page_limit) and next_page_url:
                        current_url = urljoin(self.start_url, next_page_url)
                    else:
                        current_url = None
                        next_page = False

                    retry_count = 0

                    self.logger.info(
                        'current_page ' + str(current_page) +
                        ' page_limit ' + str(page_limit) +
                        ' next_page ' + str(current_url) +
                        ' program will be sleep ' + str(sleep_time) + ' second.')

                    print('\t', 'current_page', current_page, 'page_limit', page_limit, 'next_page', current_url,
                          'program will be sleep', sleep_time, 'second.')
                elif retry_count < retry_times:

                    self.logger.info(
                        'status_code ' + str(resp.status_code) +
                        ' resp ' + str(resp.text) +
                        ' url ' + str(current_url) +
                        ' program will be sleep ' + str(sleep_time) + ' second.')

                    print('\t',
                          'status_code', resp.status_code,
                          'resp', resp.text,
                          'url', current_url,
                          'program will be sleep', sleep_time, 'second.')

                    sess = requests.Session()
                    retry_count = retry_count + 1

                else:
                    next_page = False
                # print(archives_info_dict)
                if next_page:
                    time.sleep(sleep_time)

                page_count = page_count + 1

        except Exception as e:
            print(e)
            sess = requests.Session()
            self.logger.info(str(e))


class XICISpider(object):

    def init_config(self, config):
        print(config)
        self.config = config
        self.start_url = config['start_url']
        self.headers = config['headers']
        self.timeout = config['timeout']
        self.sleep_interval_func = gen_sleep_interval_func(config['sleep_interval_mu_factor'], config['sleep_interval_min'])
        self.input_names = config['input_names']
        self.output_names = config['output_names']
        self.output_queue = config['output_queue']
        self.regx = re.compile('\s+')

        self.init_logger()
        print('at XICISpider:init_config()')
        self.logger.info('at XICISpider:init_config()')

    def init_logger(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s-%(levelname)s-%(message)s',
            datefmt='%y-%m-%d %H:%M',
            filename='./log.txt',
            filemode='a')
        self.logger = logging.getLogger()

    def get_pages(self, html):
        page_html = html.find('div', class_='pagination')
        current_page = self.regx.sub('', page_html.find('em', class_='current').text)
        next_page = page_html.find('a', class_='next_page').attrs['href']

        return (current_page, next_page)

    def get_page_data(self, html):

        trs = html.find('table', id='ip_list').find_all('tr')
        table_head = []
        for th in trs[0].find_all('th'):
            table_head.append(self.regx.sub('', th.text))
        table_data = []
        for tr in trs[1:]:
            current_col = []
            for td in tr.find_all('td'):
                current_col.append(self.regx.sub('', td.text.lower()))
            table_data.append(current_col)
        return pd.DataFrame(table_data, columns=table_head)

    def replace_table_names(self, table_df, input_names=None, output_names=None):

        if not input_names:
            input_names = self.input_names

        if not output_names:
            output_names = self.output_names

        need_cols = table_df[input_names]
        need_cols.columns = output_names
        return need_cols

    def run(self, config, next_page=True, page_limit=-1, retry_times=3):

        print('at XICISpider.run before init_config.')

        self.init_config(config)
        print('at XICISpider.run after init_config.')
        self.logger.info('at XICISpider.run after init_config.')

        try:
            print(self.start_url)
            self.logger.info(self.start_url)

            current_url = self.start_url

            sess = requests.Session()

            page_count = 1
            retry_count = 0

            while next_page:

                print('at XICISpider.run:while')
                self.logger.info('at XICISpider.crawl:while')
                sleep_time = self.sleep_interval_func()
                # headers['Referer'] = current_url
                resp = sess.get(current_url, headers=self.headers, timeout=self.timeout)
                html = bfs(resp.text, 'html5lib')

                if resp.status_code == 200 and len(html) > 0:
                    print('at XICISpider.run:if resp.status_code')
                    for proxy in self.replace_table_names(self.get_page_data(html)).values.tolist():
                        self.output_queue.put(('spider', proxy))

                    current_page, next_page_url = self.get_pages(html)

                    if (page_limit == -1 or page_count < page_limit) and next_page_url:
                        current_url = urljoin(self.start_url, next_page_url)
                    else:
                        current_url = None
                        next_page = False

                    retry_count = 0

                    self.logger.info(
                        'current_page ' + str(current_page) +
                        ' page_limit ' + str(page_limit) +
                        ' next_page ' + str(current_url) +
                        ' program will be sleep ' + str(sleep_time) + ' second.')

                    print('\t', 'current_page', current_page, 'page_limit', page_limit, 'next_page', current_url,
                          'program will be sleep', sleep_time, 'second.')

                elif retry_count < retry_times:

                    self.logger.info(
                            'status_code ' + str(resp.status_code) +
                            ' resp ' + str(resp.text) +
                            ' url ' + str(current_url) +
                            ' program will be sleep ' + str(sleep_time) + ' second.')

                    print('\t',
                          'status_code', resp.status_code,
                          'resp', resp.text,
                          'url', current_url,
                          'program will be sleep', sleep_time, 'second.')

                    sess = requests.Session()
                    retry_count = retry_count + 1

                else:
                    next_page = False

                # print(archives_info_dict)
                if next_page:
                    time.sleep(sleep_time)

                page_count = page_count + 1
        except Exception as e:
            sess = requests.Session()
            print(e)
            self.logger.info(str(e))

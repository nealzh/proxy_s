#!/usr/bin/python
# coding: UTF-8

import re
import time
import random
import pandas as pd
import logging
import requests

from bs4 import BeautifulSoup as bfs
from faker import Faker
from urllib.parse import urljoin
from multiprocessing import Process


class Spider(object):

    def __init__(self, config):

        self.config = config
        self.start_url = config['start_url']
        self.headers = config['headers']
        self.timeout = config['timeout']
        self.sleep_interval_mu_factor = config['sleep_interval_mu_factor']
        self.sleep_interval_min = config['sleep_interval_min']
        self.input_names = config['input_names']
        self.output_names = config['output_names']
        # self.output_queue = config['output_queue']
        # self.active_proxies_queue = config['active_proxies_queue']
        self.class_name = config['class_name']
        self.page_limit = config['page_limit']
        self.retry_times = config['retry_times']
        self.use_proxy = config['use_proxy']
        self.page_data_item_name = config['page_data_item_name']
        self.page_data_item_attrs = config['page_data_item_attrs']
        self.regx = re.compile('\s+')
        print('self.faker = Faker(locale=zh_CN)')
        # self.ua = UserAgent()
        self.faker = Faker(locale='zh_CN')

        self.init_logger()
        print('at ', self.class_name, ':__init__()')

    def init_logger(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s-%(levelname)s-%(message)s',
            datefmt='%y-%m-%d %H:%M',
            filename='./log.txt',
            filemode='a')
        self.logger = logging.getLogger()

    def get_sleep_interval(self):
        t = int(random.random() * self.sleep_interval_mu_factor) / 1.0
        return t if t > self.sleep_interval_min else self.sleep_interval_min

    def gen_user_agent(self):

        random_index = random.randint(0, 4)
        user_agent = ''
        if random_index == 0:
            user_agent = self.faker.internet_explorer()
        elif random_index == 1:
            user_agent = self.faker.opera()
        elif random_index == 2:
            user_agent = self.faker.chrome()
        elif random_index == 3:
            user_agent = self.faker.firefox()
        elif random_index == 4:
            user_agent = self.faker.safari()
        return user_agent

    def get_active_proxy(self):

        if self.active_proxies_queue.qsize() > 0:
            proxy_info = self.active_proxies_queue.get_nowait()

            if proxy_info:
                return {proxy_info[2] : proxy_info[0] + ':' + proxy_info[1]}
        return None

    def get_page_data(self, html):

        table = html.find(self.page_data_item_name, attrs=self.page_data_item_attrs)
        # print(table)
        table_head = []
        table_data = []
        if table:
            ths = table.find_all('th')
            if ths:
                for th in ths:
                    table_head.append(self.regx.sub('', th.text))
            tbody = table.find('tbody')
            if tbody:
                trs = tbody.find_all('tr')
                # print(len(trs))
                for tr in trs:
                    current_col = []
                    for td in tr.find_all('td'):
                        current_col.append(self.regx.sub('', td.text.lower()))
                    table_data.append(current_col)

        return pd.DataFrame(table_data, columns=table_head)

    def replace_table_names(self, table_df, input_names=None, output_names=None):

        if len(table_df) > 0:
            if not input_names:
                input_names = self.input_names

            if not output_names:
                output_names = self.output_names

            need_cols = table_df[input_names]
            need_cols.columns = output_names
            return need_cols
        else:
            return table_df

    def start_spider(self, proxies_spider_queue, active_proxies_queue):

        self.output_queue = proxies_spider_queue
        self.active_proxies_queue = active_proxies_queue
        self.start()

    def run(self):

        try:
            current_url = self.start_url
            print('self.start_url', self.start_url)
            page_count = 1
            next_page = True

            while next_page:

                current_page_status = False
                run_count = 0

                while run_count <= self.retry_times and (not current_page_status):

                    run_count = run_count + 1
                    sleep_time = self.get_sleep_interval()
                    # self.headers['Referer'] = current_url
                    self.headers['User-Agent'] = self.gen_user_agent()

                    if self.use_proxy and run_count < self.retry_times:
                        proxy_dict = self.get_active_proxy()
                    else:
                        proxy_dict = None

                    if self.use_proxy and proxy_dict is not None:
                        if self.active_proxies_queue.qsize() > 20:
                            sleep_time = random.randint(1, 5)

                    print('at ', self.class_name,
                          '.run while run_count', run_count,
                          'current_page_status', current_page_status,
                          'use proxy', proxy_dict,
                          'current_url', current_url)

                    try:
                        resp = requests.get(current_url, headers=self.headers, proxies=proxy_dict, timeout=self.timeout)
                    except Exception as inner_e:
                        print('at ', self.class_name, '.run: inner Exception', str(inner_e),
                              'proxy', proxy_dict,
                              'program will be sleep', sleep_time * page_count, 'seconds.')
                        time.sleep(sleep_time * page_count)
                        continue

                    if resp.status_code != 200 or len(resp.text) == 0:
                        print('at ', self.class_name, '.run resp.status_code', resp.status_code,
                              'resp.text', resp.text,
                              'program will be sleep', sleep_time * page_count, 'seconds.')
                        time.sleep(sleep_time * page_count)
                        continue

                    current_page_status = True

                if current_page_status and len(resp.text) > 0:

                    html = bfs(resp.text, 'html5lib')
                    for proxy_info in self.replace_table_names(self.get_page_data(html)).values.tolist():
                        # print('spider', proxy)
                        self.output_queue.put(('spider', proxy_info))

                    current_page, next_page_url = self.get_pages(html)
                    print('at ', self.class_name, '.run resp.get_pages',
                          'current_page', current_page,
                          'next_page_url', next_page_url)

                    if (self.page_limit == -1 or page_count < self.page_limit) and next_page_url:
                        current_url = urljoin(self.start_url, next_page_url)
                        page_count = page_count + 1
                    else:
                        current_url = None
                        next_page = False
                else:
                    current_url = None
                    next_page = False

                if next_page:
                    print('at ', self.class_name, '.run next_page program will be sleep', sleep_time, 'second.')
                    time.sleep(sleep_time)

        except Exception as e:
            print('at ', self.class_name, '.run: outter Exception', str(e),
                  'program will be stop.')
            # sess = requests.Session()


class KUAISpider(Spider, Process):

    def __init__(self, config):
        Process.__init__(self)
        Spider.__init__(self, config)

    def get_pages(self, html):

        page_html = html.find('div', id='listnav')
        if page_html:
            a_list = page_html.find_all('a')
            if len(a_list) > 0:
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
                        else:
                            current_page = None
                            next_page = None
                    else:
                        current_page = None
                        next_page = None
            else:
                current_page = None
                next_page = None
        else:
            current_page = None
            next_page = None

        return (current_page, next_page)


class XILASpider(Spider, Process):

    def __init__(self, config):
        Process.__init__(self)
        Spider.__init__(self, config)

    def get_pages(self, html):

        page_html = html.find('ul', class_='pagination justify-content-center')
        if page_html:
            current_page_a = page_html.find('a', class_='page-link text-black-50')
            if current_page_a:
                current_page = self.regx.sub('', current_page_a.text)

            lis = page_html.find_all('li')
            if len(lis) > 1:
                if 'class' in lis[-1].attrs:
                    if lis[-1].attrs['class'] == 'page-item' and lis[-1].text == '下一页':
                        next_page_a = lis[-1].find('a')
                        if next_page_a:
                            next_page = next_page_a.attrs['href']
                        else:
                            next_page = None
                    else:
                        next_page = None
                else:
                    next_page = None
            else:
                next_page = None
        else:
            current_page = None
            next_page = None

        return (current_page, next_page)

    def replace_table_names(self, table_df, input_names=None, output_names=None):

        if len(table_df) > 0:

            if not input_names:
                input_names = self.input_names

            if not output_names:
                output_names = self.output_names

            proxy_list = []

            need_cols_values_list = table_df[input_names].values.tolist()
            for col_value in need_cols_values_list:
                ip_port = col_value[0].split(':')
                ip = ip_port[0]
                port = ip_port[1]

                for p_type in col_value[1][0: -2].split(','):
                    proxy_list.append([ip, port, p_type])

            need_cols = pd.DataFrame(proxy_list, columns=output_names)

            return need_cols
        else:
            return table_df


class XICISpider(Spider, Process):

    def __init__(self, config):
        Process.__init__(self)
        Spider.__init__(self, config)

    def get_pages(self, html):

        page_html = html.find('div', class_='pagination')

        if page_html:
            current_page_em = page_html.find('em', class_='current')
            if current_page_em:
                current_page = self.regx.sub('', current_page_em.text)
            else:
                current_page = None

            next_page_a = page_html.find('a', class_='next_page')
            if next_page_a:
                next_page = next_page_a.attrs['href']
            else:
                next_page = None

        return (current_page, next_page)

    def get_page_data(self, html):

        table = html.find(self.page_data_item_name, attrs=self.page_data_item_attrs)
        # print(table)
        table_head = []
        table_data = []
        if table:
            ths = table.find_all('th')
            if ths:
                for th in ths:
                    table_head.append(self.regx.sub('', th.text))
            tbody = table.find('tbody')
            if tbody:
                trs = tbody.find_all('tr')
                # print(len(trs))
                for tr in trs[1 : ]:
                    current_col = []
                    for td in tr.find_all('td'):
                        current_col.append(self.regx.sub('', td.text.lower()))
                    table_data.append(current_col)

        return pd.DataFrame(table_data, columns=table_head)


class JXLSpider(Spider, Process):

    def __init__(self, config):
        Process.__init__(self)
        Spider.__init__(self, config)

    def get_pages(self, html):

        page_html = html.find('ul', class_='pagination')
        if page_html:

            current_page_li = page_html.find('li', class_='active')
            if current_page_li:
                current_page = self.regx.sub('', current_page_li.text)
            else:
                current_page = None

            next_page_a = page_html.find('a', attrs={'rel': 'next'})

            if next_page_a:
                next_page = next_page_a.attrs['href']
            else:
                next_page = None
        else:
            current_page = None
            next_page = None

        return (current_page, next_page)

    def replace_table_names(self, table_df, input_names=None, output_names=None):

        if len(table_df) > 0:

            if not input_names:
                input_names = self.input_names

            if not output_names:
                output_names = self.output_names

            need_cols = table_df[table_df['匿名度'] == '高匿'][input_names]
            need_cols.columns = output_names
            return need_cols
        else:
            return table_df

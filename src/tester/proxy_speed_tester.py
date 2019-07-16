#!/usr/bin/python
# coding: UTF-8

import time
import logging
import requests

from threading import Thread

class ProxySpeedTester(object):

    def init_config(self, config):
        self.config = config
        self.http_url = config['http']['url']
        self.http_headers = config['http']['headers']
        self.http_timeout = config['http']['timeout']
        self.https_url = config['https']['url']
        self.https_headers = config['https']['headers']
        self.https_timeout = config['https']['timeout']
        self.input_queue = config['input_queue']
        self.output_queue = config['output_queue']
        # self.process_num = config['process_num']
        self.test_limit = config['test_limit']
        self.sleep_interval = config['sleep_interval']
        self.test_thread_num = config['test_thread_num']
        self.test_thread_dict = dict()

        self.init_logger()

    def init_logger(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s-%(levelname)s-%(message)s',
            datefmt='%y-%m-%d %H:%M',
            filename='./log.txt',
            filemode='a')
        self.logger = logging.getLogger()

    def run(self, config, ):

        self.init_config(config)

        try:
            self.logger.info('at ProxySpeedTester.run before while True.')
            print('at ProxySpeedTester.run before while True.')

            while True:

                input_queue_size = self.input_queue.qsize()
                # current_thread_list = list()

                stop_thread_name_list = list()
                for k_name, v_thread in self.test_thread_dict.items():
                    if not v_thread.isAlive():
                        stop_thread_name_list.append(k_name)

                for stn in stop_thread_name_list:
                    self.test_thread_dict.pop(stn)

                print('\tat ProxySpeedTester.run:remove', len(stop_thread_name_list), 'stopped test threads.')

                print('\tat ProxySpeedTester.run:current proxies_spider_queue length', input_queue_size,
                      'test_thread_size', len(self.test_thread_dict))

                free_test_thread_num = self.test_thread_num - len(self.test_thread_dict)

                if input_queue_size > 0 and free_test_thread_num > 0:

                    for i in range(input_queue_size if input_queue_size < free_test_thread_num else free_test_thread_num):

                        source, proxy = self.input_queue.get_nowait()

                        # print(source, proxy)

                        if proxy is not None:
                            thread_name = '_'.join(proxy)

                            if thread_name not in self.test_thread_dict:

                                thread = Thread(target=self.run_test,
                                                args=(source, proxy, thread_name),
                                                name=thread_name)
                                thread.start()
                            self.test_thread_dict[thread_name] = thread
                print('\tat ProxySpeedTester.run:current proxies_spider_queue length', input_queue_size,
                      'test_thread_size', len(self.test_thread_dict), 'after add test threads.')

                time.sleep(self.sleep_interval)

        except Exception as e:
                print('at ProxySpeedTester.run:except', str(e))
                self.logger.info(str(e))

    def run_test(self, source, proxy, thread_name):

        proxies_speed_dict = self.speed_test({proxy[2].lower(): proxy[0] + ':' + proxy[1]})

        proxy_info = list()
        proxy_info.extend(proxy)

        proxy_active = False

        if 'avg_speed' in proxies_speed_dict:

            proxy_info.append(proxies_speed_dict['avg_resp_time'])
            proxy_info.append(proxies_speed_dict['avg_speed'])

            proxy_active = True

        elif 'avg_resp_time' in proxies_speed_dict:

            proxy_info.append(proxies_speed_dict['avg_resp_time'])
            proxy_info.append(0.0)

        else:
            proxy_info.append(0.0)
            proxy_info.append(0.0)

        # print('\tthread', thread_name, 'testing result:', proxy_info)

        if proxy_active or source == 'persisent':
            # print('\tproxy_speed_tester:', tuple(proxy_info))
            self.output_queue.put((source, proxy_active, tuple(proxy_info)))

    def speed_test(self, proxies):

        count = 0

        proxy_test_dict = dict()
        test_detail_list = list()

        sum_ctime = 0
        sum_speed = 0

        count_ctime = 0
        count_speed = 0

        if 'http' in proxies:
            url = self.http_url
            headers = self.http_headers
            timeout = self.http_timeout
        elif 'https' in proxies:
            url = self.https_url
            headers = self.https_headers
            timeout = self.https_timeout

        while count < self.test_limit:

            test_detail = dict()

            try:
                f_time = time.time()
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                c_time = time.time() - f_time

                test_detail['status_code'] = resp.status_code
                test_detail['resp_time'] = c_time

                sum_ctime = sum_ctime + c_time
                count_ctime = count_ctime + 1

                proxy_test_dict['avg_resp_time'] = round(sum_ctime / count_ctime, 3)

                if resp.status_code == 200:
                    speed = len(resp.content) / c_time
                    test_detail['speed'] = speed
                    sum_speed = sum_speed + speed
                    count_speed = count_speed + 1

                    proxy_test_dict['avg_speed'] = round((sum_speed / count_speed) / 1024, 3)

            except Exception as e:
                test_detail['exception'] = e

            test_detail_list.append(test_detail)

            count = count + 1

        proxy_test_dict['detail'] = test_detail_list

        return proxy_test_dict

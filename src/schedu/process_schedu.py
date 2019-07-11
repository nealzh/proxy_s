#!/usr/bin/python
# coding: UTF-8

import sys

#dev
sys.path.append('G:/workspace/python/proxy_s')
#online
#sys.path.append('/home/zhangli/workspace/python/user_trace_server')

import time

from src.spider import KUAISpider, XICISpider
from src.tester import ProxySpeedTester
from src.persistent import ProxyPresisenter
from src.config import site_spider_config, speed_test_config, persisent_config, schedu_config
from multiprocessing import Pool, Manager, Process


class ProcessSchedu(object):

    def __init__(self, config):
        self.spider_queue_len = config['spider_queue_len']
        self.test_queue_len = config['test_queue_len']
        self.processes_pool_size = config['processes_pool_size']

    def run(self, sleep_interval=15):

        try:

            process_pool = Pool(processes=self.processes_pool_size)

            process_manager = Manager()
            proxies_spider_queue = process_manager.Queue(self.spider_queue_len)
            proxies_test_queue = process_manager.Queue(self.test_queue_len)

            site_spider_config['kuaidaili_inha']['output_queue'] = proxies_spider_queue
            site_spider_config['xicidaili_nn']['output_queue'] = proxies_spider_queue

            kuai = KUAISpider()
            xici = XICISpider()

            speed_test_config['input_queue'] = proxies_spider_queue
            speed_test_config['output_queue'] = proxies_test_queue

            pst = ProxySpeedTester()

            persisent_config['input_queue'] = proxies_test_queue
            persisent_config['output_queue'] = proxies_spider_queue

            pp = ProxyPresisenter()

            process_pool.apply_async(pst.run, (speed_test_config,))
            process_pool.apply_async(pp.run, (persisent_config,))
            process_pool.apply_async(xici.run, (site_spider_config['xicidaili_nn'], ))
            process_pool.apply_async(kuai.run, (site_spider_config['kuaidaili_inha'], ))

            while True:

                psq_size = proxies_spider_queue.qsize()
                ptq_size = proxies_test_queue.qsize()

                print('psq_size', psq_size, 'ptq_size', ptq_size)

                time.sleep(sleep_interval)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    ps = ProcessSchedu(schedu_config)
    ps.run()

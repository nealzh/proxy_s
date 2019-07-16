#!/usr/bin/python
# coding: UTF-8

import sys

#dev
sys.path.append('G:/workspace/python/proxy_s')
#online
#sys.path.append('/home/zhangli/workspace/python/user_trace_server')

import time

from src.spider import KUAISpider, XICISpider, XILASpider, JXLSpider
from src.tester import ProxySpeedTester
from src.persistent import ProxyPresisenter
from src.config import site_spider_config, speed_test_config, persisent_config, schedu_config
from multiprocessing import Queue
from multiprocessing import Pool, Manager


class ProcessSchedu(object):

    def __init__(self, config):
        self.spider_queue_len = config['spider_queue_len']
        self.test_queue_len = config['test_queue_len']
        self.active_proxy_queue_len = config['active_proxy_queue_len']
        self.processes_pool_size = config['processes_pool_size']

    def run(self, sleep_interval=15):

        try:

            process_pool = Pool(processes=self.processes_pool_size)

            process_manager = Manager()
            proxies_spider_queue = process_manager.Queue(self.spider_queue_len)
            proxies_test_queue = process_manager.Queue(self.test_queue_len)

            active_proxies_queue = process_manager.Queue(self.active_proxy_queue_len)

            # site_spider_config['kuaidaili_inha']['output_queue'] = proxies_spider_queue
            # site_spider_config['kuaidaili_inha']['active_proxies_queue'] = active_proxies_queue
            #
            # site_spider_config['xicidaili_nn']['output_queue'] = proxies_spider_queue
            # site_spider_config['xicidaili_nn']['active_proxies_queue'] = active_proxies_queue
            #
            # site_spider_config['xiladaili_gaoni']['output_queue'] = proxies_spider_queue
            # site_spider_config['xiladaili_gaoni']['active_proxies_queue'] = active_proxies_queue
            #
            # site_spider_config['jiangxianli']['output_queue'] = proxies_spider_queue
            # site_spider_config['jiangxianli']['active_proxies_queue'] = active_proxies_queue

            kuai = KUAISpider(site_spider_config['kuaidaili_inha'])
            xici = XICISpider(site_spider_config['xicidaili_nn'])
            xila = XILASpider(site_spider_config['xiladaili_gaoni'])
            jxl = JXLSpider(site_spider_config['jiangxianli'])

            speed_test_config['input_queue'] = proxies_spider_queue
            speed_test_config['output_queue'] = proxies_test_queue

            pst = ProxySpeedTester()

            persisent_config['input_queue'] = proxies_test_queue
            persisent_config['output_queue'] = proxies_spider_queue

            pp = ProxyPresisenter()

            pp2 = ProxyPresisenter()
            pp2.init_config(persisent_config)

            process_pool.apply_async(pst.run, (speed_test_config,))
            process_pool.apply_async(pp.run, (persisent_config,))
            # process_pool.apply_async(xici.run, (site_spider_config['xicidaili_nn'], ))
            # process_pool.apply_async(kuai.run, (site_spider_config['kuaidaili_inha'], ))
            # process_pool.apply_async(xila.run, (site_spider_config['xiladaili_gaoni'],))
            # process_pool.apply_async(jxl.run, (site_spider_config['jiangxianli'],))

            xici.start_spider(proxies_spider_queue, active_proxies_queue)
            kuai.start_spider(proxies_spider_queue, active_proxies_queue)
            xila.start_spider(proxies_spider_queue, active_proxies_queue)
            jxl.start_spider(proxies_spider_queue, active_proxies_queue)

            print('at ProcessSchedu.run:before while True.')

            while True:

                self.set_spider_active_proxies(pp2, active_proxies_queue)
                psq_size = proxies_spider_queue.qsize()
                ptq_size = proxies_test_queue.qsize()

                print('psq_size', psq_size, 'ptq_size', ptq_size)

                time.sleep(sleep_interval)
        except Exception as e:
            print('at ProcessSchedu.run:except', str(e))

    def set_spider_active_proxies(self, pp, active_proxies_queue):

        if active_proxies_queue.qsize() < self.active_proxy_queue_len / 2:

            column_names, active_list = pp.select_active_proxy()

            for active_proxy_info in active_list:
                if active_proxies_queue.qsize() < self.active_proxy_queue_len - 1:
                    # print(active_proxy_info)
                    # print(tuple(active_proxy_info))
                    active_proxies_queue.put_nowait(tuple(active_proxy_info))
                else:
                    break


if __name__ == "__main__":
    ps = ProcessSchedu(schedu_config)
    ps.run()

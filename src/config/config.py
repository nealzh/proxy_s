#!/usr/bin/python
# coding: UTF-8

#代理测速配置
timeout = 60
output_names = ['ip', 'port', 'p_type']

#http 测速配置
http_test_header = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding' : 'gzip, deflate',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Cache-Control' : 'max-age=0',
    'Connection' : 'keep-alive',
    'Host' : 'www.265.com',
    'Upgrade-Insecure-Requests' : '1',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

http_test_url = 'http://www.265.com/'

http_test_config = dict()
http_test_config['url'] = http_test_url
http_test_config['headers'] = http_test_header
http_test_config['timeout'] = 15

#https 测速配置
https_test_header = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding' : 'gzip, deflate, br',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Cache-Control' : 'max-age=0',
    'Connection' : 'keep-alive',
    'Host' : 'www.baidu.com',
    'Upgrade-Insecure-Requests' : '1',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}
https_test_url = 'https://www.baidu.com/'

https_test_config = dict()
https_test_config['url'] = https_test_url
https_test_config['headers'] = https_test_header
https_test_config['timeout'] = 15

speed_test_config = dict()
speed_test_config['http'] = http_test_config
speed_test_config['https'] = https_test_config
speed_test_config['test_thread_num'] = 64

speed_test_config['test_limit'] = 1
speed_test_config['sleep_interval'] = 2

#快代理高匿配置
kuaidaili_inha_url = 'https://www.kuaidaili.com/free/inha/'
kuaidaili_inha_header = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding' : 'gzip, deflate, br',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Cache-Control' : 'max-age=0',
    'Connection' : 'keep-alive',
    'Host' : 'www.kuaidaili.com',
    'Referer' : 'https://www.kuaidaili.com/free/',
    'Upgrade-Insecure-Requests' : '1',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

kuaidaili_inha_input_names = ['IP', 'PORT', '类型']

kuaidaili_inha_config = dict()
kuaidaili_inha_config['start_url'] = kuaidaili_inha_url
kuaidaili_inha_config['headers'] = kuaidaili_inha_header
kuaidaili_inha_config['timeout'] = timeout
kuaidaili_inha_config['sleep_interval_mu_factor'] = 30
kuaidaili_inha_config['sleep_interval_min'] = 10

kuaidaili_inha_config['input_names'] = kuaidaili_inha_input_names
kuaidaili_inha_config['output_names'] = output_names

#西刺代理高匿配置
xicidaili_nn_url = 'https://www.xicidaili.com/nn/'
xicidaili_nn_header = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding' : 'gzip, deflate, br',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Cache-Control' : 'max-age=0',
    'Connection' : 'keep-alive',
    'Host' : 'www.xicidaili.com',
    'If-None-Match' : 'W/"89a50a0f6011ce3e33ecf74d4ebc68f7"',
    'Referer' : 'https://www.xicidaili.com/nn/',
    'Upgrade-Insecure-Requests' : '1',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

xicidaili_inha_input_names = ['IP地址', '端口', '类型']

xicidaili_nn_config = dict()
xicidaili_nn_config['start_url'] = xicidaili_nn_url
xicidaili_nn_config['headers'] = xicidaili_nn_header
xicidaili_nn_config['timeout'] = timeout
xicidaili_nn_config['sleep_interval_mu_factor'] = 60
xicidaili_nn_config['sleep_interval_min'] = 15
xicidaili_nn_config['input_names'] = xicidaili_inha_input_names
xicidaili_nn_config['output_names'] = output_names

#网站爬虫配置
site_spider_config = dict()

site_spider_config['kuaidaili_inha'] = kuaidaili_inha_config
site_spider_config['xicidaili_nn'] = xicidaili_nn_config

#mysql 配置
mysql_host = 'ip'
mysql_port = 3306
mysql_db = 'db'
mysql_user = 'db'
mysql_passwd = 'passwd'
mysql_charset = 'utf8'

mysql_config = dict()
mysql_config['host'] = mysql_host,
mysql_config['port'] = mysql_port,
mysql_config['db'] = mysql_db,
mysql_config['user'] = mysql_user,
mysql_config['passwd'] = mysql_passwd
mysql_config['charset'] = mysql_charset
mysql_config['conn_pool_mincached'] = 2
mysql_config['conn_pool_maxcached'] = 8


#持久化参数配置
persisent_batch_size = 512
persisent_table_name = 'active_proxy'
persisent_sleep_interval = 15
persisent_active_update_seconds = 180
persisent_inactive_update_seconds = 600
persisent_inactive_del_seconds = 7200

persisent_config = dict()

persisent_config['batch_size'] = persisent_batch_size
persisent_config['table_name'] = persisent_table_name
persisent_config['active_update_seconds'] = persisent_active_update_seconds
persisent_config['inactive_update_seconds'] = persisent_inactive_update_seconds
persisent_config['inactive_del_seconds'] = persisent_inactive_del_seconds
persisent_config['sleep_interval'] = persisent_sleep_interval
persisent_config['storage_config'] = mysql_config

schedu_spider_queue_len = 8192
schedu_test_queue_len = 8192
schedu_processes_pool_size = 8

schedu_config = dict()
schedu_config['spider_queue_len'] = schedu_spider_queue_len
schedu_config['test_queue_len'] = schedu_test_queue_len
schedu_config['processes_pool_size'] = schedu_processes_pool_size

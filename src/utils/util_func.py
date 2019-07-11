#!/usr/bin/python
# coding: UTF-8

import time

def add_double_quotation(s, dq='"%s"'):
    return dq % str(s)

def ip_2_int(ip):
    return sum([256 ** j * int(i) for j, i in enumerate(ip.split('.')[::-1])])

def int_2_ip(num):
    return '.'.join([str(int(num / (256 ** i) % 256)) for i in range(3, -1, -1)])

def get_datetime_str(format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format)

def gen_sleep_interval_func(mu_factor=30, min_interval=5):
    import random
    def sleep_interval_func(mu_factor=mu_factor, min_interval=min_interval):
        t = int(random.random() * mu_factor) / 1.0
        return t if t > min_interval else min_interval
    return sleep_interval_func

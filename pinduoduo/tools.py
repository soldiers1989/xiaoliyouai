# -*- coding:utf-8 -*-
__author__ = '张全亮'
# 可以封装成函数，方便 Python 的程序调用
import socket


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


if __name__ == '__main__':
    get_host_ip()

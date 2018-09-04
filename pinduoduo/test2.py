# -*- coding:utf-8 -*-
__author__ = '张全亮'
import csv
import random

f = open('用户地址.csv', 'r', encoding='utf-8')
b = f.readlines()[random.randint(0, 6500)]
name = str(b.split(',')[0]).replace('"', '').replace("'", '')
phone = str(b.split(',')[1]).replace('"', '').replace("'", '')
address = str(b.split(',')[2:-3]).replace('"', '').replace("'", '').replace("[", '').replace("]", '').replace(",", '')
province_id = str(b.split(',')[-3]).replace('"', '').replace("'", '')
city_id = str(b.split(',')[-2]).replace('"', '').replace("'", '')
district_id = str(b.split(',')[-1].replace('\n', '')).replace('"', '').replace("'", '')
f.close()
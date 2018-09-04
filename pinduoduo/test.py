# -*- coding:utf-8 -*-
__author__ = '张全亮'
from mysql_db import db_insert, db_query
import datetime
with open('地址库.txt', 'r') as f:
    for a in f.readlines():
        add_list = a.replace('\n', '').split('|')
        province = add_list[0]
        city = add_list[1]
        district = add_list[2]
        address = str(add_list[3: -2]).replace('|', '').replace('[', '').replace(']', '').replace("'", '')
        name = add_list[-2]
        phone = add_list[-1]
        print(province, city, district, address, name, phone)
        sql = "select province, province_id, city, city_id, district, district_id from pdd_address " \
              "where province='{}' and city='{}' and district='{}'".format(province, city, district)
        result = db_query(sql)
        if len(result) == 0:
            print('无无')
            continue
        create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('result', result)
        sql2 = "insert into user_address(name, phone, address, province, province_id, city, city_id, district, district_id, create_time)" \
              " values ('{}', '{}','{}', '{}', '{}','{}', '{}', '{}', '{}', '{}')".\
            format(name, phone, address, result[0][0], result[0][1], result[0][2], result[0][3], result[0][4],
                   result[0][5], create_time)
        print(sql2)
        db_insert(sql2)
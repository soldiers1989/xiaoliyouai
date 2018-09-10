# -*- coding:utf-8 -*-
__author__ = '张全亮'
import csv
import requests
from mysql_db import db_query
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')
end_time = today + ' 23:59:59'


# TODO 我的下单
def order_down():
    sql = "select DISTINCT pdduid, amount, accesstoken, goods_url,order_number, orderno,  notifyurl, sign, goods_id, callbackurl,extends, is_use  from t_acc_order" \
          " where create_time BETWEEN '{}' and '{}' ".format(today, end_time)
    result_list = db_query(sql)

    for result in result_list:
        if result[11] == 0:
            is_use = '否'
        else:
            is_use = '是'

        data = {
            "name": result[0],
            "amount": result[1],
            "token": result[2],
            "goods_url": result[3],
            "goods_number": result[4],
            "orderno": result[5],
            "notifyurl": result[6],
            "sign": result[7],
            "order": is_use,
            "goods_id": result[8],
            "callbackurl": result[9],
            "extends": result[10]
        }
        url = 'http://127.0.0.1:8000/api/pay/'
        response = requests.post(url, json=data)
        print(response.json())
       

# TODO 我的订单
def order():
    sql = "select DISTINCT pdduid, orderno, order_sn, amount, order_type, pay_url,  status from t_acc_order" \
          " where create_time BETWEEN '{}' and '{}' ".format(today, end_time)
    result_list = db_query(sql)
    for result in result_list:
        if result[6] == 0:
            status = '已失效'
        elif result[6] == 1:
            status = '待支付'
        elif result[6] == 2:
            status = '待发货'
        else:
            status = '已评价'
        if status == '已评价':
            evalute = '是'
        else:
            evalute = '否'
        data = {
            "name": result[0],
            "orderno": result[1],
            "order_sn": result[2],
            "amount": result[3],
            "order_type": result[4],
            "pay_url": result[5],
            "status": status,
            "evalute": evalute
        }
        url = 'http://127.0.0.1:8000/api/order/'
        response = requests.post(url, json=data)
        print(response.json())


# TODO 我的评价
def evaluate():
    sql = "select distinct pdduid, goods_id, goods_url, order_sn from t_acc_order where status=3 and  create_time BETWEEN '{}' and '{}' ".format(
        today, end_time)
    result_list = db_query(sql)
    for result in result_list:
        data = {
            "name": result[0],
            "goods_id": result[1],
            "goods_url": result[2],
            "order_sn": result[3],
            "content": "商品太好了，买了几百次",
            "over": '是'
        }
        url = 'http://127.0.0.1:8000/api/evaluate/'
        response = requests.post(url, json=data)
        print(response.json())


if __name__ == '__main__':
    order_down()
    order()
    evaluate()

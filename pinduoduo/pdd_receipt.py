# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()
import re, datetime, time
from logger import Logger
from mysql_db import db_insert
from redis_queue import RedisQueue

q = RedisQueue('pdd')
r = RedisQueue('rec')
logger = Logger()

"""自动5星好评"""


def evaluation(pdduid, accesstoken, goods_id, order_sn):
    url = 'https://mobile.yangkeduo.com/proxy/api/v2/order/goods/review?pdduid={}'.format(pdduid)
    cookie = 'pdd_user_id={}; PDDAccessToken={};'.format(pdduid, accesstoken)
    headers = {
        'accesstoken': accesstoken,
        'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0',
        'Cookie': cookie
    }
    data = {
        "goods_id": goods_id,
        "order_sn": order_sn,
        "desc_score": 5,
        "logistics_score": 5,
        "service_score": 5,
        "comment": "商品特别好，已经买过很多次了.",
        "pictures": [],
        "labels": []
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if 'review_id' in response.json() and 'share_code' in response.json():
        return True
    else:
        return False


"""自动确认收货"""


def confirm_receipt(accesstoken, pdduid, order_sn):
    url = 'https://mobile.yangkeduo.com/proxy/api/order/{}/received?pdduid={}&is_back=1'.format(order_sn, pdduid)
    cookie = 'pdd_user_id={}; PDDAccessToken={};'.format(pdduid, accesstoken)
    headers = {
        'accesstoken': accesstoken,
        'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0',
        'Cookie': cookie
    }
    for i in range(3):
        try:
            response = requests.post(url, headers=headers, verify=False)
            if 'nickname' in response.json() and 'share_code' in response.json():
                return True
            else:
                return False
        except:
            continue


"""校验支付状态"""


def check_pay(order_sn, pdduid, accesstoken):
    cookie = 'pdd_user_id={}; PDDAccessToken={};'.format(pdduid, accesstoken)
    headers = {
        'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0',
        'Cookie': cookie
    }
    url = 'https://mobile.yangkeduo.com/personal_order_result.html?page=1&size=10&keyWord={}'.format(order_sn)
    res = requests.get(url, headers=headers, verify=False)

    if 'window.isUseHttps= false' in res.text or 'window.isUseHttps' not in res.text:
        logger.log('ERROR', '查询订单:[{}]错误'.format(order_sn), 'receipt', pdduid)
        return '查询订单:[{}]错误'.format(order_sn)
    else:
        n_order_sn = re.findall('"order_sn":"(.*?)",', res.text)[0]
        if order_sn == n_order_sn:
            # try:
            #     pay_status = re.findall('"order_status_desc":"(.*?)",', res.text)[0]
            # except:
            #     pay_status = re.findall('"order_status_prompt":"(.*?)",', res.text)[0]
            soup = BeautifulSoup(res.text, 'html.parser')
            pay_status = soup.find('p', class_='order-status').get_text().strip()
            logger.log('INFO', '获取订单:[{}]信息成功, 支付状态: {}'.format(n_order_sn, pay_status), 'status', pdduid)
            return pay_status
        else:
            logger.log('ERROR', '查询订单:[{}]错误'.format(order_sn), 'receipt', pdduid)
            return '查询订单:[{}]错误, 请确认!'.format(order_sn)


"""自动发货"""


def confirm_delivery(order_sn, passid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        "PASSID": passid,
        "Content-Type": "application/json"
    }
    data1 = {"orderSn": order_sn, "source": "MMS"}
    url = 'https://mms.pinduoduo.com/mars/shop/orderDetail'
    response1 = requests.post(url, json=data1, headers=headers, verify=False)
    if 'success' in response1.json():
        url2 = 'https://mms.pinduoduo.com/express_base/shop/orders/shipping'
        data2 = {"orderShipRequestList": [{"orderSn": order_sn}],
                 "isSingleShipment": 1,
                 "overWrite": 1,
                 "operateFrom": "MMS",
                 "functionType": 6,
                 "isVirtualGoods": "true"}
        response2 = requests.post(url2, json=data2, headers=headers, verify=False)
        if 'success' in response2.json():
            logger.log('INFO', '订单:[{}]已经自动发货了'.format(order_sn), 'receipt', 'Admin')
            return True
        else:
            print(response2.json())
            logger.log('ERROR', '订单:[{}]发货失败, 请联系管理员'.format(order_sn), 'receipt', 'Admin')
            return False
    elif '会话已过期' in response1.json():
        logger.log('DEBUG', '订单:[{}]发货失败, 请更新passid'.format(order_sn), 'receipt', 'Admin')
        return False
    else:
        print(response1.json())
        logger.log('ERROR', '订单:[{}]发货失败, 请联系管理员'.format(order_sn), 'receipt', 'Admin')
        return False


"""订单的相关校验"""


def check(result):
    q_order_sn = result['order_sn']
    pdduid = result['pdduid']
    accesstoken = result['accesstoken']
    goods_id = result['goods_id']
    passid = result['passid']

    update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['is_use'] = 2
    result['update_time'] = update_time

    status = check_pay(q_order_sn, pdduid, accesstoken)
    if '已评价' in status or '待评价' in status or '已收货' in status:
        result['status'] = 3
        result['is_query'] = 0
        result['update_time'] = update_time
        result['success'] = True
        return result
    elif '待支付' in status:
        q.put(result)
        return result
    elif '待发货' in status:
        """自动发货"""
        is_ok = confirm_delivery(q_order_sn, passid)
        if is_ok is False:
            r.put(result)
            return result
    elif '待收货' in status:
        pass
    else:
        logger.log('ERROR', '订单:[{}]未考虑到的订单类型: {}'.format(q_order_sn, status), 'receipt', pdduid)

    if confirm_receipt(accesstoken, pdduid, q_order_sn):
        logger.log('INFO', '订单:[{}]已确认收货'.format(q_order_sn), 'receipt', pdduid)
        if evaluation(pdduid, accesstoken, goods_id, q_order_sn):
            logger.log('INFO', '订单:[{}]已5星好评'.format(q_order_sn), 'receipt', pdduid)
        else:
            logger.log('DEBUG', '订单:[{}]5星好评错误'.format(q_order_sn), 'receipt', pdduid)
        update_time2 = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['status'] = 3
        result['is_query'] = 0
        result['update_time'] = update_time2
        result['success'] = True
    else:
        r.put(result)
        logger.log('ERROR', '订单:[{}]收货错误'.format(q_order_sn), 'receipt', pdduid)
    return result


"""拼多多确认收货入口函数"""


def main():
    r_result = r.get_nowait()
    if not r_result:
        return
    r_dict = eval(r_result)

    # 状态为已失效和不查询的时候，保持这笔失效订单
    if r_dict['status'] == 0 and r_dict['is_query'] == 0:
        sql = "insert into t_acc_order (accesstoken, amount, goods_url, goods_id, orderno, order_number, pdduid, notifyurl, callbackurl," \
              " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, passid, is_use, create_time, update_time)" \
              " values ('{}', '{}','{}', '{}','{}','{}', '{}','{}', '{}', '{}', '{}','{}', '{}','{}', '{}','{}', '{}', '{}','{}','{}', '{}')". \
            format(r_dict['accesstoken'], r_dict['amount'], r_dict['goods_url'], r_dict['goods_id'], r_dict['orderno'],
                   r_dict['order_number'], r_dict['pdduid'], r_dict['notifyurl'], r_dict['callbackurl'],
                   r_dict['extends'],
                   r_dict['sign'], r_dict['order_type'], r_dict['pay_url'], r_dict['order_sn'], r_dict['status'],
                   r_dict['is_query'], r_dict['memberid'], r_dict['passid'], r_dict['is_use'],
                   r_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S'), r_dict['create_time'])
        db_insert(sql)
    else:
        result = check(r_dict)
        # 发货失败和收货失败的情况下，重新添加队列，查询
        if result['success'] is True and result['is_query'] == 1:
            return
        # 发货成功收货成功，数据入库，出队
        elif result['success'] is True and result['is_query'] == 0:
            sql = "insert into t_acc_order (accesstoken, amount, goods_url, goods_id, orderno, order_number, pdduid, notifyurl, callbackurl," \
                  " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, passid, is_use, create_time, update_time)" \
                  " values ('{}', '{}','{}', '{}','{}','{}', '{}','{}', '{}', '{}', '{}','{}', '{}','{}', '{}','{}', '{}', '{}','{}','{}', '{}')". \
                format(result['accesstoken'], result['amount'], result['goods_url'], result['goods_id'],
                       result['orderno'],
                       result['order_number'], result['pdduid'], result['notifyurl'], result['callbackurl'],
                       result['extends'],
                       result['sign'], result['order_type'], result['pay_url'], result['order_sn'], result['status'],
                       result['is_query'], result['memberid'], result['passid'], result['is_use'],
                       result['create_time'].strftime('%Y-%m-%d %H:%M:%S'), result['create_time'])
            db_insert(sql)
        # 其它情况下，重新添加队列，查询
        else:
            r.put(result)


if __name__ == '__main__':
    logger.log('INFO', '确认收货脚本启动...', 'receipt', 'Admin')
    while True:
        try:
            main()
        except Exception as ex:
            logger.log('ERROR', '程序异常，异常原因: [{}],重启...'.format(ex), 'receipt', 'Admin')
            time.sleep(10)
            continue
        time.sleep(1)

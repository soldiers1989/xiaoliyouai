# -*- coding:utf-8 -*-
__author__ = '张全亮'
from multiprocessing.dummy import Pool
import re, datetime, time
from logger import Logger
from mysql_db import db_insert
from redis_queue import RedisQueue
import requests
import math
import urllib3

urllib3.disable_warnings()

yz = RedisQueue('yz')
yz_rec = RedisQueue('yz_rec')
logger = Logger()
"""自动5星好评"""


def evaluation(kdtsessionid, goods_id, sku_id, q_order_sn):
    cookie = 'KDTSESSIONID={}'.format(kdtsessionid)
    url = 'https://h5.youzan.com/v2/trade/reviews/reviews.json'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        'Cookie': cookie
    }
    data = {
        "order_no": q_order_sn,
        "goods_id": goods_id,
        "sku_id": sku_id,
        "rate": 30,
        "desc_rate": 5,
        "serv_rate": 5,
        "logi_rate": 5,
        "review": "商品特别好，买了很多次"
    }
    response = requests.post(url, headers=headers, data=data, verify=False)
    if '已经评价过' in str(response.json()):
        return True
    elif '评价提交成功' in str(response.json()):
        return True
    else:
        return False


"""自动确认收货"""


def confirm_receipt(q_order_sn, kdtsessionid, pdduid):
    cookie = 'KDTSESSIONID={}'.format(kdtsessionid)
    url = 'https://h5.youzan.com/v2/trade/order/confirmReceive.json?order_no={}'.format(q_order_sn)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
        'Cookie': cookie
    }
    response = requests.get(url, headers=headers, verify=False)
    if '收货失败' not in str(response.json()):
        logger.log('INFO', '订单:[{}]已确认收货'.format(q_order_sn), 'yz_receipt', pdduid)
        return True
    else:
        if '40201' in response.text:
            logger.log('INFO', '订单:[{}]收货失败, 无法正常收货{}'.format(q_order_sn, response.json()), 'yz_receipt', pdduid)
        else:
            logger.log('INFO', '订单:[{}]收货失败, {}'.format(q_order_sn, response.json()), 'yz_receipt', pdduid)
        return False


"""自动以快递方式为其它 发货"""


def confirm_delivery(order_sn, cookie, pdduid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        'Cookie': cookie
    }
    address_url = 'https://www.youzan.com/v2/trade/order/orderItems.json?order_no={}'.format(order_sn)
    res = requests.get(address_url, headers=headers, verify=False)
    if 'success' in res.text and 'items' in res.text:
        item_id = 0
        item_id_list = res.json()['data']['items']
        for item in item_id_list:
            item_id = item['item_id']
        url = 'https://www.youzan.com/v2/trade/order/express.json'
        data = {
            "order_no": order_sn,
            "express_type": 0,
            "no_express": 1,
            "item_ids[]": item_id
        }
        response = requests.post(url, headers=headers, data=data, verify=False)

        if '订单已经发过货了' in str(response.json()):
            logger.log('INFO', '订单:[{}]已经发过货了'.format(order_sn), 'yz_receipt', pdduid)
            return True
        elif 'success' in str(response.json()):
            logger.log('INFO', '订单:[{}]已经发货成功.'.format(order_sn), 'yz_receipt', pdduid)
            return True
        else:
            logger.log('INFO', '订单:[{}]已经发货失败.'.format(order_sn), 'yz_receipt', pdduid)
            return False
    else:
        if '订单不存在' in str(res.json()):
            logger.log('ERROR', '发货失败 订单不存在', 'yz_receipt', pdduid)
            return False
        else:
            logger.log('ERROR', '发货失败，请联系管理员' + res.text, 'yz_receipt', pdduid)
            return False


"""校验支付状态"""


def check_pay(order_sn, pdduid, kdtsessionid):
    cookie = 'KDTSESSIONID={}'.format(kdtsessionid)
    firsr_url = 'https://h5.youzan.com/v2/trade/order/list.json?perpage=20&page=1&type=all'
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
        'Cookie': cookie
    }
    res = requests.get(firsr_url, headers=headers, verify=False)
    if '页面已被删除' in res.text:
        logger.log('ERROR', 'kdtsessionid参数错误, 网页未找到', 'yz_receipt', pdduid)
        return 'kdtsessionid参数错误, 网页未找到'
    total = res.json()['data']['total']
    page = math.ceil(total / 20)
    for i in range(page):
        url = 'https://h5.youzan.com/v2/trade/order/list.json?perpage=20&page={}&type=all'.format(i + 1)
        response = requests.get(url, headers=headers, verify=False)
        if 'data' not in response.text and 'list' not in response.text:
            logger.log('ERROR', '查找订单错误, 请确认.', 'yz_receipt', order_sn)
            return '查找订单错误, 请确认.'
        res_json = response.json()
        for j in res_json['data']['list']:
            if j['order_no'] == order_sn:
                logger.log('INFO', '订单:[{}]状态 {}'.format(order_sn, j['order_state_str']), 'yz_receipt', pdduid)
                order_state = j['order_state_str']
                return order_state
            else:
                continue
    return '查找订单:[{}]错误'.format(order_sn)


"""校验主流程"""


def check(result):
    q_order_sn = result['order_sn']
    pdduid = result['pdduid']
    kdtsessionid = result['kdtsessionid']
    goods_id = result['goods_id']
    sku_id = result['sku_id']
    cookie = result['cookie']

    update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['is_use'] = 2
    result['update_time'] = update_time

    status = check_pay(q_order_sn, pdduid, kdtsessionid)
    if '已评价' in status or '待评价' in status or '已收货' in status or '交易完成' in status:
        result['status'] = 3
        result['is_query'] = 0
        result['update_time'] = update_time
        result['success'] = True
        return result
    elif '等待买家付款' in status:
        yz.put(result)
        return result
    elif '待发货' in status or '买家已付款' in status:
        """自动发货"""
        is_ok = confirm_delivery(q_order_sn, cookie, pdduid)
        if is_ok is False:
            yz_rec.put(result)
            return result
    elif '已发货' in status:
        pass
    else:
        logger.log('ERROR', '订单:[{}]未考虑到的订单类型: {}'.format(q_order_sn, status), 'yz_receipt', pdduid)

    """自动确认收货"""
    if confirm_receipt(q_order_sn, kdtsessionid, pdduid):
        """自动5星好评"""
        if evaluation(kdtsessionid, goods_id, sku_id, q_order_sn):
            logger.log('INFO', '订单:[{}]已5星好评'.format(q_order_sn), 'yz_receipt', pdduid)
        else:
            logger.log('DEBUG', '订单:[{}]5星好评错误'.format(q_order_sn), 'yz_receipt', pdduid)
        update_time2 = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['status'] = 3
        result['is_query'] = 0
        result['update_time'] = update_time2
        result['success'] = True
    else:
        yz_rec.put(result)
    return result


def yz_main():
    r_result = yz_rec.get_nowait()
    if not r_result:
        return
    r_dict = eval(r_result)
    # 状态为已失效和不查询的时候，保持这笔失效订单
    if r_dict['status'] == 0 and r_dict['is_query'] == 0:
        sql = "insert into t_yz_order (kdtsessionid, amount, goods_url, goods_id, orderno, order_number, user_id, notifyurl, callbackurl," \
              " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, cookie, is_use, create_time, update_time)" \
              " values ('{}', '{}','{}', '{}','{}','{}', '{}','{}', '{}', '{}', '{}','{}', '{}','{}', '{}','{}', '{}', '{}','{}','{}', '{}')". \
            format(r_dict['kdtsessionid'], r_dict['amount'], r_dict['goods_url'], r_dict['goods_id'], r_dict['orderno'],
                   r_dict['order_number'], r_dict['pdduid'], r_dict['notifyurl'], r_dict['callbackurl'],
                   r_dict['extends'],
                   r_dict['sign'], r_dict['order_type'], r_dict['pay_url'], r_dict['order_sn'], r_dict['status'],
                   r_dict['is_query'], r_dict['memberid'], r_dict['cookie'], r_dict['is_use'],
                   r_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S'), r_dict['create_time'])
        db_insert(sql)
    else:
        result = check(r_dict)
        # 发货失败和收货失败的情况下，重新添加队列，查询
        if result['success'] is True and result['is_query'] == 1:
            return
        # 发货成功收货成功，数据入库，出队
        elif result['success'] is True and result['is_query'] == 0:
            sql = "insert into t_yz_order (kdtsessionid, amount, goods_url, goods_id, orderno, order_number, user_id, notifyurl, callbackurl," \
                  " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, cookie, is_use, create_time, update_time)" \
                  " values ('{}', '{}','{}', '{}','{}','{}', '{}','{}', '{}', '{}', '{}','{}', '{}','{}', '{}','{}', '{}', '{}','{}','{}', '{}')". \
                format(result['kdtsessionid'], result['amount'], result['goods_url'], result['goods_id'],
                       result['orderno'],
                       result['order_number'], result['pdduid'], result['notifyurl'], result['callbackurl'],
                       result['extends'],
                       result['sign'], result['order_type'], result['pay_url'], result['order_sn'], result['status'],
                       result['is_query'], result['memberid'], result['cookie'], result['is_use'],
                       result['create_time'].strftime('%Y-%m-%d %H:%M:%S'), result['create_time'])
            db_insert(sql)
        # 其它情况下，重新添加队列，查询
        else:
            yz_rec.put(result)


if __name__ == '__main__':
    logger.log('INFO', '检测订单脚本启动...', 'yz_receipt', 'Admin')
    while True:
        qsize = yz_rec.qsize()
        if qsize == 0:
            time.sleep(3)
            continue
        if qsize < 100:
            pool = Pool(processes=qsize)
        else:
            pool = Pool(processes=100)
        for i in range(qsize):
            try:
                pool.apply_async(yz_main)
            except Exception as ex:
                logger.log('ERROR', '程序异常，异常原因: [{}],重启...'.format(ex), 'yz_receipt', 'Admin')
                time.sleep(10)
                continue
        pool.close()
        pool.join()
        time.sleep(3)

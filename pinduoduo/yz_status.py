# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import urllib3
import math
import time
import datetime
from multiprocessing.dummy import Pool

import hashlib

urllib3.disable_warnings()
from logger import Logger
from redis_queue import RedisQueue

yz = RedisQueue('yz')
yz_rec = RedisQueue('yz_rec')
logger = Logger()
"""校验订单规则，每页查找订单,找到符合条件的结束翻页查找"""


def check_pay(order_sn, pdduid, kdtsessionid):
    cookie = 'KDTSESSIONID={}'.format(kdtsessionid)
    firsr_url = 'https://h5.youzan.com/v2/trade/order/list.json?perpage=20&page=1&type=all'
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
        'Cookie': cookie
    }
    res = requests.get(firsr_url, headers=headers, verify=False)
    if '页面已被删除' in res.text:
        logger.log('ERROR', 'kdtsessionid参数错误, 网页未找到', 'yz_status', pdduid)
        return 'kdtsessionid参数错误, 网页未找到'
    total = res.json()['data']['total']
    page = math.ceil(total / 20)
    for i in range(page):
        url = 'https://h5.youzan.com/v2/trade/order/list.json?perpage=20&page={}&type=all'.format(i + 1)
        response = requests.get(url, headers=headers, verify=False)
        if 'data' not in response.text and 'list' not in response.text:
            logger.log('ERROR', '查找订单:[{}]错误, 请确认.'.format(order_sn), 'yz_status', pdduid)
            return '查找订单错误, 请确认.'
        res_json = response.json()
        for j in res_json['data']['list']:
            if j['order_no'] == order_sn:
                logger.log('INFO', '订单:[{}]状态 {}'.format(order_sn, j['order_state_str']), 'yz_status', pdduid)
                order_state = j['order_state_str']
                return order_state
            else:
                continue
    return '查找订单:[{}]错误'.format(order_sn)


"""检验支付状态"""


def check(result):
    kdtsessionid = result['kdtsessionid']
    pdduid = result['pdduid']
    notifyurl = result['notifyurl']
    orderno = result['orderno']
    amount = result['amount']
    extends = result['extends']
    order_number = result['order_number']
    update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['is_use'] = 1  # 修改调用状态为被status调用
    result['update_time'] = update_time  # 修改更新时间
    result['success'] = False
    result['msg'] = ''
    q_order_sn = result['order_sn']
    order_state = check_pay(q_order_sn, pdduid, kdtsessionid)
    if '待发货' in order_state or '已发货' in order_state or '已付款' in order_state:  # TODO
        result['status'] = 2  # 修改支付状态为待发货
        result['success'] = True

        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'
        a = 'amount={}&code=1&order_number={}&orderno={}&status=1&key={}'. \
            format(amount, order_number, orderno, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()

        logger.log('INFO', '加密后的字符串: {}'.format(encrypt), 'yz_status', pdduid)
        data = {
            "code": 1,
            "msg": "",
            "status": 1,
            "orderno": orderno,
            "order_number": order_number,
            "amount": amount,
            "extends": extends,
            "sign": encrypt
        }
        for j in range(6):
            response = requests.post(notifyurl, data=data, verify=False)
            print('回调返回: ', response.json())
            if response.json()['code'] == 1:
                logger.log('INFO', '订单:[{}]支付结果正常返回'.format(q_order_sn), 'yz_status', pdduid)
                return result
            if j == 5:
                logger.log('ERROR', '订单:[{}]支付结果未正常返回'.format(q_order_sn), 'yz_status', pdduid)
                return result
            time.sleep(300)
            logger.log('INFO', '订单:[{}]在{}分钟内未正确回调'.format(q_order_sn, (j + 1) * 5), 'yz_status', pdduid)
    elif '错误' in order_state:
        result['msg'] = order_state
        return result
    else:
        return result


"""有赞检验订单入口函数"""


def yz_main():
    q_result = yz.get_nowait()
    if not q_result:
        return
    q_dict = eval(q_result)
    q_time = q_dict['create_time'] + datetime.timedelta(minutes=60)
    result = check(q_dict)
    if '错误' in result['msg']:
        logger.log('ERROR', result, 'yz_status', result['pdduid'])
        yz.put(q_result)
        return
    # 如果6分钟后的时间和当前时间比较，如果比现在的时间大，则不添加队列
    if q_time > datetime.datetime.now() and result['success'] is False:
        logger.log('INFO', '订单:[{}]支付状态未改变, 重新添加进队列:[yz]'.format(result['order_sn']), 'queue', result['pdduid'])
        yz.put(q_result)
    else:
        if result['success']:
            logger.log('INFO', '订单:[{}]支付状态已改变, 添加进队列:[yz_rec]'.format(result['order_sn']), 'queue', result['pdduid'])
            yz_rec.put(result)
        else:
            result['status'] = 0
            result['is_query'] = 0
            logger.log('DEBUG', '订单:[{}]6分钟内支付状态未改变, 添加进队列:[yz_rec]'.format(result['order_sn']), 'queue',
                       result['pdduid'])
            yz_rec.put(result)


if __name__ == '__main__':
    logger.log('INFO', '检测订单脚本启动...', 'yz_status', 'Admin')
    while True:
        qsize = yz.qsize()
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
                logger.log('ERROR', '程序异常，异常原因: [{}],重启...'.format(ex), 'yz_status', 'Admin')
                time.sleep(10)
                continue
        pool.close()
        pool.join()
        time.sleep(3)

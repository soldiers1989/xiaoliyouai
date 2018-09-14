# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import urllib3
import hashlib
from redis_queue import RedisQueue
from bs4 import BeautifulSoup
from multiprocessing.pool import Pool

urllib3.disable_warnings()
import re, datetime, time
from logger import Logger

pdd = RedisQueue('pdd')
pdd_rec = RedisQueue('pdd_rec')
logger = Logger()

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
        logger.log('ERROR', '查询订单:[{}]错误'.format(order_sn), 'pdd_status', pdduid)
        return '查询订单:[{}]错误'.format(order_sn)
    else:
        n_order_sn = re.findall('"order_sn":"(.*?)",', res.text)[0]
        if order_sn == n_order_sn:
            soup = BeautifulSoup(res.text, 'html.parser')
            pay_status = soup.find('p', class_='order-status').get_text().strip()
            logger.log('INFO', '获取订单:[{}]信息成功, 支付状态: {}'.format(n_order_sn, pay_status), 'pdd_status', pdduid)
            return pay_status
        else:
            logger.log('ERROR', '查询订单:[{}]错误'.format(order_sn), 'pdd_status', pdduid)
            return '查询订单:[{}]错误, 请确认!'.format(order_sn)


"""校验订单状态"""


def check(result):
    q_order_sn = result['order_sn']
    pdduid = result['pdduid']
    accesstoken = result['accesstoken']
    notifyurl = result['notifyurl']
    orderno = result['orderno']
    amount = result['amount']
    extends = result['extends']
    order_number = result['order_number']
    update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['is_use'] = 1  # 修改调用状态为被status调用
    result['update_time'] = update_time  # 修改更新时间
    result['success'] = False

    status = check_pay(q_order_sn, pdduid, accesstoken)
    if '待发货' in status or '拼团成功' in status or '待收货' in status or '已评价' in status:
        result['status'] = 2  # 修改支付状态为待发货
        result['success'] = True

        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'
        a = 'amount={}&code=1&order_number={}&orderno={}&status=1&key={}'. \
            format(amount, order_number, orderno, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()

        logger.log('INFO', '加密后的字符串: {}'.format(encrypt), 'pdd_status', pdduid)
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
                logger.log('INFO', '订单:[{}]支付结果正常返回'.format(q_order_sn), 'pdd_status', pdduid)
                return result
            if j == 5:
                logger.log('ERROR', '订单:[{}]支付结果未正常返回'.format(q_order_sn), 'pdd_status', pdduid)
                return result
            time.sleep(300)
            logger.log('INFO', '订单:[{}]在{}分钟内未正确回调'.format(q_order_sn, (j + 1) * 5), 'pdd_status', pdduid)
    else:
        return result


"""拼多多校验订单状态入口函数"""


def pdd_main():
    q_result = pdd.get_nowait()
    if not q_result:
        return
    q_dict = eval(q_result)
    q_time = q_dict['create_time'] + datetime.timedelta(minutes=6)
    result = check(q_dict)
    # 如果6分钟后的时间和当前时间比较，如果比现在的时间大，则不添加队列
    if q_time > datetime.datetime.now() and result['success'] is False:
        logger.log('INFO', '订单:[{}]支付状态未改变, 重新添加进队列:[pdd]'.format(result['order_sn']), 'queue', result['pdduid'])
        pdd.put(q_result)
    else:
        if result['success']:
            logger.log('INFO', '订单:[{}]支付状态已改变, 添加进队列:[pdd_rec]'.format(result['order_sn']), 'queue', result['pdduid'])
            pdd_rec.put(result)
        else:
            result['status'] = 0
            result['is_query'] = 0
            logger.log('DEBUG', '订单:[{}]6分钟内支付状态未改变, 添加进队列:[pdd_rec]'.format(result['order_sn']), 'queue',
                       result['pdduid'])
            pdd_rec.put(result)


if __name__ == '__main__':
    logger.log('INFO', '检测订单脚本启动...', 'pdd_status', 'Admin')
    while True:
        qsize = pdd.qsize()
        if qsize == 0:
            time.sleep(3)
            continue
        if qsize < 100:
            pool = Pool(processes=qsize)
        else:
            pool = Pool(processes=100)
        for i in range(qsize):
            try:
                pool.apply_async(pdd_main)
            except Exception as ex:
                logger.log('ERROR', '程序异常，异常原因: [{}],重启...'.format(ex), 'pdd_status', 'Admin')
                time.sleep(10)
                continue
        pool.close()
        pool.join()
        time.sleep(3)

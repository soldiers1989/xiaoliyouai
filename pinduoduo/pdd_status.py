# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import urllib3
import hashlib
import threading
from multiprocessing.dummy import Pool

urllib3.disable_warnings()
import re, datetime, time, json
from logger import Logger
from mysql_db import db_query, db_insert

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
        logger.log('ERROR', '查询订单[{}]错误'.format(order_sn), 'status', pdduid)
        return '查询订单[{}]错误'.format(order_sn)
    else:
        n_order_sn = re.findall('"order_sn":"(.*?)",', res.text)[0]
        if order_sn == n_order_sn:
            pay_status = re.findall('"order_status_desc":"(.*?)",', res.text)[0]
            logger.log('INFO', '获取订单[{}]信息成功, 支付状态: {}'.format(n_order_sn, pay_status), 'status', pdduid)
            return pay_status
        else:
            logger.log('ERROR', '查询订单[{}]错误'.format(order_sn), 'status', pdduid)
            return '查询订单[{}]错误, 请确认!'.format(order_sn)


"""校验订单状态"""


def check(result):
    logger.log('INFO', '开始校验订单:{}支付状态'.format(result[0]), 'status', result[1])
    for i in range(61):
        q_order_sn = result[0]
        pdduid = result[1]
        accesstoken = result[2]
        notifyurl = result[3]
        orderno = result[4]
        amount = result[5]
        extends = result[6]
        order_number = result[7]
        update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "update t_acc_order set is_use=1, update_time='{}' where order_sn='{}'".format(update_time, q_order_sn)
        db_insert(sql)
        status = check_pay(q_order_sn, pdduid, accesstoken)
        if '待发货' in status or '拼团成功' in status or '待收货' in status or '已评价' in status:
            # update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update t_acc_order set status=2, update_time='{}' where order_sn='{}'".format(update_time,
                                                                                                 q_order_sn)
            db_insert(sql)
            key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'
            a = 'amount={}&code=1&order_number={}&orderno={}&status=1&key={}'. \
                format(amount, order_number, orderno, key)
            hl = hashlib.md5()
            hl.update(str(a).encode('utf-8'))
            encrypt = str(hl.hexdigest()).upper()

            logger.log('INFO', '加密后的字符串: {}'.format(encrypt), 'status', pdduid)
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
                    logger.log('INFO', '订单[{}], 支付结果正常返回'.format(q_order_sn), 'status', pdduid)
                    break
                if j == 5:
                    logger.log('ERROR', '订单[{}], 支付结果未正常返回'.format(q_order_sn), 'status', pdduid)
                    break
                time.sleep(300)
                logger.log('INFO', '订单:{}在{}分钟内未正确回调'.format(q_order_sn, (j + 1) * 5), 'status', pdduid)
            return

        if i == 60:
            update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update t_acc_order set status=0, is_query=0, update_time='{}' where order_sn='{}'".format(
                update_time, q_order_sn)
            db_insert(sql)
            logger.log('DEBUG', '订单[{}], 设定时间内,支付状态未改变,不在查询此订单'.format(q_order_sn), 'status', pdduid)
            return
        time.sleep(5)
        logger.log('INFO', '在{}秒内, 订单: [{}], 支付状态未改变.'.format((i + 1) * 5, q_order_sn), 'status', pdduid)


"""拼多多校验订单状态入口函数"""


def main():
    query_sql = "select order_sn, pdduid, accesstoken, notifyurl, orderno, amount, extends, order_number, memberid, passid from t_acc_order" \
                " where status='1' and is_query='1' and is_use='0' LIMIT 50"

    result = db_query(query_sql)
    logger.log('INFO', '查询数据库符合条件的结果, 共[{}]个'.format(len(result)), 'status', 'Admin')
    if len(result) == 0:
        return
    pool = Pool(processes=50)
    for j in result:
        pool.apply_async(check, [j])
    pool.close()
    pool.join()


if __name__ == '__main__':
    logger.log('INFO', '检测订单脚本启动...', 'status', 'Admin')
    while True:
        try:
            main()
        except Exception as ex:
            logger.log('ERROR', '程序异常，异常原因: [{}],重启...'.format(ex), 'status', 'Admin')
            time.sleep(10)
            continue
        time.sleep(10)

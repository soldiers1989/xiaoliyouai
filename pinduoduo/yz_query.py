# -*- coding:utf-8 -*-
__author__ = '张全亮'
# 可以封装成函数，方便 Python 的程序调用
from mysql_db import db_query, db_insert
from redis_queue import RedisQueue
import datetime

yz = RedisQueue('yz')
yz_rec = RedisQueue('yz_rec')


def r_dict(result):
    r_result = {
        'kdtsessionid': result[0],
        'amount': result[1],
        'goods_url': result[2],
        'goods_id': result[3],
        'orderno': result[4],
        'order_number': result[5],
        'pdduid': result[6],
        'notifyurl': result[7],
        'callbackurl': result[8],
        'extends': result[9],
        'sign': result[10],
        'order_type': result[11],
        'pay_url': result[12],
        'order_sn': result[13],
        'status': result[14],
        'is_query': result[15],
        'memberid': result[16],
        'cookie': result[17],
        'is_use': result[18],
        'create_time': result[19],
        'update_time': result[20]
    }
    return r_result


# TODO 通过字段条件来补单, 失效订单不考虑补单
def yz_pass_field(**kwargs):
    res = ''
    for k, v in kwargs.items():
        res += k + '=' + str(v) + " and "
    where_r = res.rstrip(' and ')
    # 查出满足条件的数据
    q_sql = "select kdtsessionid, amount, goods_url, goods_id, orderno, order_number, user_id, notifyurl, callbackurl," \
            " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, cookie, is_use, create_time, update_time from t_yz_order where {}".format(
        where_r)
    result_list = db_query(q_sql)
    # # 将满足条件的数据删除
    # d_sql = "delete from t_yz_order where {}".format(where_r)
    # db_insert(d_sql)

    for result in result_list:
        r_result = r_dict(result)
        yz_rec.put(r_result)
        print(r_result)


# TODO 通过时间段来补单, 失效订单不考虑补单
def yz_pass_date(**kwargs):
    res = ''
    for k, v in kwargs.items():
        res += v + '|'
    where_r = res.rstrip('|')
    q_sql = "select kdtsessionid, amount, goods_url, goods_id, orderno, order_number, user_id, notifyurl, callbackurl," \
            " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, cookie, is_use, create_time, update_time from t_yz_order" \
            " where create_time BETWEEN '{}' and '{}' ".format(where_r.split('|')[0], where_r.split('|')[1])
    result_list = db_query(q_sql)
    # 将满足条件的数据删除
    # d_sql = "delete from t_yz_order where create_time BETWEEN '{}' and '{}' ".format(where_r.split('|')[0],
    #                                                                                   where_r.split('|')[1])
    # db_insert(d_sql)
    for result in result_list:
        r_result = r_dict(result)
        yz_rec.put(r_result)
        print(r_result)


def yz_pass_query(pdduid=None, orderno=None, order_sn=None):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    end_time = today + ' 23:59:59'
    if pdduid is None and orderno is None and order_sn is None:
        sql = "select orderno, status from t_yz_order  where create_time BETWEEN '{}' and '{}' ".format(today,
                                                                                                         end_time)
    elif pdduid is None and orderno is None and order_sn is not None:
        sql = "select orderno, status from t_yz_order where order_sn='{}'".format(order_sn)
    elif pdduid is None and orderno is not None and order_sn is None:
        sql = "select orderno, status from t_yz_order where orderno='{}'".format(orderno)
    elif pdduid is not None and orderno is None and order_sn is None:
        sql = "select orderno, status from t_yz_order where user_id='{}'".format(pdduid)
    elif pdduid is not None and orderno is not None and order_sn is None:
        sql = "select orderno, status from t_yz_order where user_id='{}' and orderno='{}'".format(pdduid, orderno)
    elif pdduid is not None and orderno is None and order_sn is not None:
        sql = "select orderno, status from t_yz_order where user_id='{}' and order_sn='{}'".format(pdduid, order_sn)
    elif pdduid is None and orderno is not None and order_sn is not None:
        sql = "select orderno, status from t_yz_order where orderno='{}' and order_sn='{}'".format(orderno, order_sn)
    else:
        sql = "select orderno, status from t_yz_order where user_id='{}' and orderno='{}' and order_sn='{}'".format(
            pdduid, orderno, order_sn)
    try:
        q_result = db_query(sql)
        result = []
        for j in q_result:
            result_dict = {}
            result_dict['code'] = 1
            result_dict['orderno'] = j[0]
            result_dict['status'] = j[1]
            result.append(result_dict)
        if len(result) == 0:
            result = {'code': 0, 'msg': '未找到满足条件的订单!'}
        return result
    except:
        return {'code': 0, 'msg': '查询错误!'}


if __name__ == '__main__':
    result = yz_pass_query()
    a = []
    for j in result:
        a.append(j['orderno'])
    print(a)
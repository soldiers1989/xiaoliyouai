# -*- coding:utf-8 -*-
__author__ = '张全亮'
# 可以封装成函数，方便 Python 的程序调用\
from mysql_db import db_query, db_insert
from redis_queue import RedisQueue

q = RedisQueue('pdd')
r = RedisQueue('rec')


def r_dict(result):
    r_result = {
        'accesstoken': result[0],
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
        'passid': result[17],
        'is_use': result[18],
        'create_time': result[19],
        'update_time': result[20]
    }
    return r_result


# TODO 通过字段条件来补单, 失效订单不考虑补单
def pass_field(**kwargs):
    res = ''
    for k, v in kwargs.items():
        res += k + '=' + str(v) + " and "
    where_r = res.rstrip(' and ')
    # 查出满足条件的数据
    q_sql = "select accesstoken, amount, goods_url, goods_id, orderno, order_number, pdduid, notifyurl, callbackurl," \
            " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, passid, is_use, create_time, update_time from t_acc_order where {}".format(
        where_r)
    result_list = db_query(q_sql)
    # 将满足条件的数据删除
    d_sql = "delete from t_acc_order where {}".format(where_r)
    db_insert(d_sql)

    for result in result_list:
        r_result = r_dict(result)
        r.put(r_result)
        print(r_result)


# TODO 通过时间段来补单, 失效订单不考虑补单
def pass_date(**kwargs):
    res = ''
    for k, v in kwargs.items():
        res += v + '|'
    where_r = res.rstrip('|')
    q_sql = "select accesstoken, amount, goods_url, goods_id, orderno, order_number, pdduid, notifyurl, callbackurl," \
            " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, passid, is_use, create_time, update_time from t_acc_order" \
            " where create_time BETWEEN '{}' and '{}' ".format(where_r.split('|')[0], where_r.split('|')[1])
    result_list = db_query(q_sql)
    # 将满足条件的数据删除
    d_sql = "delete from t_acc_order where create_time BETWEEN '{}' and '{}' ".format(where_r.split('|')[0],
                                                                                      where_r.split('|')[1])
    db_insert(d_sql)

    for result in result_list:
        r_result = r_dict(result)
        r.put(r_result)
        print(r_result)


if __name__ == '__main__':
    # pass_field(is_query=0, status=0)
    pass_date(start_date='2018-01-01', end_date='2018-10-08')

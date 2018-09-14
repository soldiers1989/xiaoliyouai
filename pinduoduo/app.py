import hashlib
import datetime
from mysql_db import db_insert
from flask import Flask, jsonify, request, redirect, render_template
from redis_queue import RedisQueue

app = Flask(__name__)

# 下单部分
from pdd_spider import pdd_main
from yz_spider import yz_main

# 查询部分
from pdd_query import pdd_pass_query
from yz_query import yz_pass_query

pdd = RedisQueue('pdd')
yz = RedisQueue('yz')

"""拼多多下单爬虫"""


def pdd_spider(pdduid, accesstoken, goods_url, amount, order_number):
    result = pdd_main(pdduid, accesstoken, goods_url, amount, order_number)
    return result


"""有赞下单爬虫"""


def yz_spider(pdduid, kdtsessionid, goods_url, amount, order_number):
    result = yz_main(pdduid, kdtsessionid, goods_url, amount, order_number)
    return result


@app.route('/')
def test():
    return 'server start success'


@app.route('/pay')
def test_pay():
    pay_url = 'weixin://wap/pay?prepayid%3Dwx031910501112006e331180633831409305&package=1777101486&noncestr=1535973050&sign=6dffd3b987985fb082663121c1171b21'
    return render_template('pay.html', pay_url=pay_url)


"""拼多多查询接口"""


@app.route('/api/query/pdd', methods=['GET', 'POST'])
def pdd_query():
    if request.method == 'GET':
        return jsonify({'code': 0, 'msg': '请求方式必须为POST'})
    else:
        form_data = request.form.to_dict()
        pdduid = form_data['pdduid'] if 'pdduid' in form_data else ''
        orderno = form_data['orderno'] if 'orderno' in form_data else ''
        order_sn = form_data['order_sn'] if 'order_sn' in form_data else ''
        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'
        a = 'order_sn={}&orderno={}&pdduid={}&key={}'.format(order_sn, orderno, pdduid, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()
        print(encrypt)
        if form_data['sign'] == encrypt:
            pdduid = None if pdduid == '' else pdduid
            orderno = None if orderno == '' else orderno
            order_sn = None if order_sn == '' else order_sn
            result = pdd_pass_query(pdduid, orderno, order_sn)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


"""有赞查询接口"""


@app.route('/api/query/yz', methods=['GET', 'POST'])
def yz_query():
    if request.method == 'GET':
        return jsonify({'code': 0, 'msg': '请求方式必须为POST'})
    else:
        form_data = request.form.to_dict()
        pdduid = form_data['pdduid'] if 'pdduid' in form_data else ''
        orderno = form_data['orderno'] if 'orderno' in form_data else ''
        order_sn = form_data['order_sn'] if 'order_sn' in form_data else ''
        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'
        a = 'order_sn={}&orderno={}&pdduid={}&key={}'.format(order_sn, orderno, pdduid, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()
        print(encrypt)
        if form_data['sign'] == encrypt:
            pdduid = None if pdduid == '' else pdduid
            orderno = None if orderno == '' else orderno
            order_sn = None if order_sn == '' else order_sn
            result = yz_pass_query(pdduid, orderno, order_sn)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


"""拼多多API"""


@app.route('/api/pay/pdd', methods=['GET', 'POST'])
def pdd_pay():
    if request.method == 'GET':
        return jsonify({'code': 0, 'msg': '请求方式必须为POST', 'order_sn': '', 'pay_url': ''})
    else:
        form_data = request.form.to_dict()
        check_data = ['accesstoken', 'amount', 'goods_url', 'orderno', 'pdduid', 'notifyurl', 'sign', 'memberid',
                      'passid', 'order_number']
        for j in check_data:
            if j not in form_data:
                return jsonify({'code': 0, 'msg': 'POST参数错误', 'order_sn': '', 'pay_url': ''})
        if 'callbackurl' in form_data:
            callbackurl = form_data['callbackurl']
        else:
            callbackurl = ''
        if 'extends' in form_data:
            extends = form_data['extends']
        else:
            extends = ''

        accesstoken = form_data['accesstoken']  # 登陆的通讯令牌
        amount = form_data['amount']  # 金额,保持两位小数
        goods_url = form_data['goods_url']  # 自己家的商品地址
        orderno = form_data['orderno']  # 自己传入的订单号
        pdduid = form_data['pdduid']  # 登陆的手机号
        notifyurl = form_data['notifyurl']
        order_number = int(form_data['order_number'])  # 下单数量
        memberid = form_data['memberid']  # 商家ID
        passid = form_data['passid']  # 发货需要的通行ID

        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'  # 签名认证的key
        a = 'accesstoken={}&amount={}&goods_url={}&memberid={}&order_number={}&orderno={}&passid={}&pdduid={}&key={}'. \
            format(accesstoken, amount, goods_url, memberid, order_number, orderno, passid, pdduid, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()

        print(encrypt)
        if form_data['sign'] == encrypt:
            result = pdd_spider(pdduid, accesstoken, goods_url, amount, order_number)
            if result['code'] == 1:
                create_time = datetime.datetime.now()
                q_result = {
                    'accesstoken': accesstoken,
                    'amount': amount,
                    'goods_url': goods_url,
                    'goods_id': result['goods_id'],
                    'orderno': orderno,
                    'order_number': order_number,
                    'pdduid': pdduid,
                    'notifyurl': notifyurl,
                    'callbackurl': callbackurl,
                    'extends': extends,
                    'sign': encrypt,
                    'order_type': 'pdd',
                    'pay_url': result['pay_url'],
                    'order_sn': result['order_sn'],
                    'status': 1,
                    'is_query': 1,
                    'memberid': memberid,
                    'passid': passid,
                    'is_use': 0,
                    'create_time': create_time,
                    'update_time': create_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                pdd.put(q_result)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


"""有赞API"""


@app.route('/api/pay/yz', methods=['GET', 'POST'])
def yz_pay():
    if request.method == 'GET':
        return jsonify({'code': 0, 'msg': '请求方式必须为POST', 'order_sn': '', 'pay_url': ''})
    else:
        form_data = request.form.to_dict()
        check_data = ['kdtsessionid', 'amount', 'goods_url', 'orderno', 'pdduid', 'notifyurl', 'sign', 'memberid',
                      'cookie', 'order_number']
        for j in check_data:
            if j not in form_data:
                return jsonify({'code': 0, 'msg': 'POST参数错误', 'order_sn': '', 'pay_url': ''})
        if 'callbackurl' in form_data:
            callbackurl = form_data['callbackurl']
        else:
            callbackurl = ''
        if 'extends' in form_data:
            extends = form_data['extends']
        else:
            extends = ''

        kdtsessionid = form_data['kdtsessionid']  # 有赞用户ID
        amount = form_data['amount']  # 金额,保持两位小数
        goods_url = form_data['goods_url']  # 自己家的商品地址
        orderno = form_data['orderno']  # 自己传入的订单号
        pdduid = form_data['pdduid']  # 登陆的手机号
        notifyurl = form_data['notifyurl']
        order_number = int(form_data['order_number'])  # 下单数量
        memberid = form_data['memberid']  # 商家ID
        cookie = form_data['cookie']  # 发货需要的cookie

        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'  # 签名认证的key
        a = 'amount={}&cookie={}&goods_url={}&kdtsessionid={}&memberid={}&order_number={}&orderno={}&pdduid={}&key={}'. \
            format(amount, cookie, goods_url, kdtsessionid, memberid, order_number, orderno, pdduid, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()

        print(encrypt)
        if form_data['sign'] == encrypt:
            result = yz_spider(pdduid, kdtsessionid, goods_url, amount, order_number)
            if result['code'] == 1:
                create_time = datetime.datetime.now()
                q_result = {
                    'kdtsessionid': kdtsessionid,
                    'amount': amount,
                    'goods_url': goods_url,
                    'goods_id': result['goods_id'],
                    'orderno': orderno,
                    'order_number': order_number,
                    'pdduid': pdduid,
                    'notifyurl': notifyurl,
                    'callbackurl': callbackurl,
                    'extends': extends,
                    'sign': encrypt,
                    'pay_url': result['pay_url'],
                    'order_sn': result['order_sn'],
                    'status': 1,
                    'is_query': 1,
                    'memberid': memberid,
                    'cookie': cookie,
                    'order_type': 'yz',
                    'is_use': 0,
                    'sku_id': result['sku_id'],
                    'create_time': create_time,
                    'update_time': create_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                yz.put(q_result)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

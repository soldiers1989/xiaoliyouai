import hashlib
import datetime
from mysql_db import db_insert
from flask import Flask, jsonify, request, redirect, render_template
from redis_queue import RedisQueue

app = Flask(__name__)

# 下单部分
from pdd_spider import main

# 查询部分
from pdd_query import pass_query

q = RedisQueue('pdd')


def spider(pdduid, accesstoken, goods_url, amount, order_number):
    result = main(pdduid, accesstoken, goods_url, amount, order_number)
    return result


@app.route('/')
def test():
    return 'server start success'


@app.route('/pay')
def test_pay():
    pay_url = 'weixin://wap/pay?prepayid%3Dwx031910501112006e331180633831409305&package=1777101486&noncestr=1535973050&sign=6dffd3b987985fb082663121c1171b21'
    return render_template('pay.html', pay_url=pay_url)


@app.route('/api/query', methods=['GET', 'POST'])
def query():
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
            result = pass_query(pdduid, orderno, order_sn)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


@app.route('/api/pay', methods=['GET', 'POST'])
def pay():
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
            result = spider(pdduid, accesstoken, goods_url, amount, order_number)
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
                q.put(q_result)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

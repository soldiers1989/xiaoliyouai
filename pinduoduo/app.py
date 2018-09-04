import hashlib
import datetime
from mysql_db import db_insert
from flask import Flask, jsonify, request, redirect, render_template

app = Flask(__name__)

# 爬虫部分
from pdd_spider import main


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


@app.route('/api/pay', methods=['GET', 'POST'])
def pay():
    if request.method == 'GET':
        return jsonify({'code': 0, 'msg': '请求方式必须为POST', 'order_sn': '', 'pay_url': ''})
    else:
        form_data = request.form.to_dict()
        check_data = ['accesstoken', 'amount', 'goods_url', 'orderno', 'pdduid', 'notifyurl', 'sign', 'memberid', 'passid']
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
        memberid = form_data['memberid']    # 商家ID
        passid = form_data['passid']    # 发货需要的通行ID

        key = 'nLSm8fdKCY6ZeysRjrzaHUgQXMp2vlJd'  # 签名认证的key
        a = 'accesstoken={}&amount={}&goods_url={}&memberid={}&order_number={}&orderno={}&passid={}&pdduid={}&key={}'. \
            format(accesstoken, amount, goods_url,  memberid, order_number, orderno, passid, pdduid, key)
        hl = hashlib.md5()
        hl.update(str(a).encode('utf-8'))
        encrypt = str(hl.hexdigest()).upper()

        print(encrypt)
        if form_data['sign'] == encrypt:
            result = spider(pdduid, accesstoken, goods_url, amount, order_number)
            if result['code'] == 1:
                create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = "insert into order_pdd (accesstoken, amount, goods_url, goods_id, orderno, order_number, pdduid, notifyurl, callbackurl," \
                      " extends, sign, order_type, pay_url, order_sn, status, is_query, memberid, passid, create_time, update_time)" \
                      " values ('{}', '{}','{}', '{}','{}','{}', '{}','{}', '{}', '{}', '{}','{}', '{}','{}', '{}','{}', '{}', '{}','{}', '{}')". \
                    format(accesstoken, amount, goods_url, result['goods_id'], orderno, order_number, pdduid, notifyurl, callbackurl,
                           extends, encrypt, 'pdd', result['pay_url'], result['order_sn'], '待支付', 1, memberid, passid, create_time,
                           create_time)
                db_insert(sql)
        else:
            result = {'code': 0, 'msg': '签名失败'}
        return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

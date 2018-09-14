# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import re
import urllib3
import urllib.parse
import random

urllib3.disable_warnings()
from logger import Logger

logger = Logger()
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
}

""" 获取添加购物车需要的商品信息, 并对金额做判断"""


def get_goods_id(goods_url, amount, cookie, order_number):
    headers['Cookie'] = cookie
    response = requests.get(goods_url, headers=headers, verify=False)
    html = response.text
    goods_list = re.findall('"list":.(.*?)]', html, re.I | re.S)
    amount_ = str((amount * 100) / order_number).split('.')[0]
    if goods_list != ['']:
        try:
            price_list = re.findall('"price":(.*?),', str(goods_list), re.I | re.S)
            sku_id_list = re.findall('"id":(.*?),', str(goods_list), re.I | re.S)
            kdt_id_list = re.findall('"kdt_id":(.*?),', str(goods_list), re.I | re.S)
            goods_id_list = re.findall('goods_id":(.*?)},', str(goods_list), re.I | re.S)
        except:
            return '提取商品列表错误', None, None
        if amount_ not in price_list:
            return '订单金额错误, 给定金额:{}'.format(amount), None, None
        for i in range(len(price_list)):
            if float(amount_) == float(price_list[i]):
                sku_id = sku_id_list[i]
                kdt_id = kdt_id_list[i]
                goods_id = goods_id_list[0]
                return sku_id, kdt_id, goods_id
            else:
                continue
    else:
        price = re.findall('"collection_price":(.*?),', html, re.I | re.S)[0]
        sku_id = re.findall('"collection_id":(.*?),', html, re.I | re.S)[0]
        goods_id = re.findall('"goods_id":"(.*?)",', html, re.I | re.S)[0]
        kdt_id = re.findall('{"kdt_id":(.*?),', html, re.I | re.S)[0]
        if float(amount_) != float(price):
            return '订单金额错误, 不一致, 给定金额:{}'.format(amount_), None, None
        return sku_id, kdt_id, goods_id


"""将购买的商品添加进购物车, 实际不需要此处理"""


def add_shop_cart(sku_id, kdt_id, goods_id, goods_number):
    url = 'https://h5.youzan.com/v2/trade/cart/goods.jsonp?kdt_id={}&goods_id={}&postage=0&num={}&activity_id=0' \
          '&activity_type=0&sku_id={}&use_wxpay=0&callback=jsonp1'.format(kdt_id, goods_id, goods_number, sku_id)
    response2 = requests.get(url, headers=headers, verify=False)
    if 'success' in response2.text:
        return True
    else:
        print(response2.text)
        return False


"""提供对应商品的sku_id, kdt_id, goods_id, goods_number可以直接下单，不需要添加进购物车"""


def pay(sku_id, kdt_id, goods_id, order_number):
    url = 'https://h5.youzan.com/v2/trade/common/cache.json'
    data1 = {
        "common": {"activity_alias": [{"goods_id": goods_id, "sku_id": sku_id}], "order_from": "cart",
                   "kdt_id": kdt_id},
        "goodsList": [
            {"goods_id": goods_id, "sku_id": sku_id, "num": order_number, "id": goods_id, 'message_0': "15478785757"}],
        "isMultiShopChecked": 0
    }
    response1 = requests.post(url, json=data1, headers=headers, verify=False)
    buy_url = response1.json()['data']['buyUrl']
    book_key = response1.json()['data']['key']
    response2 = requests.get(buy_url, headers=headers, verify=False)
    if '编号：-101' in response2.text or '登录' in response2.text:
        return False, 'kdtsessionid参数错误, 无法获取订单', ''
    client_ip = re.findall('"client_ip":"(.*?)",', response2.text)[0]
    kdt_session_id = re.findall('"kdt_session_id":"(.*?)",', response2.text)[0]

    f = open('yz用户地址.csv', 'r', encoding='utf-8')
    b = f.readlines()[random.randint(0, 6500)]
    name = str(b.split(',')[0]).replace('"', '').replace("'", '')
    phone = str(b.split(',')[1]).replace('"', '').replace("'", '')
    address = str(b.split(',')[2:-3]).replace('"', '').replace("'", '').replace("[", '').replace("]", '').replace(
        ",", '')
    province = str(b.split(',')[-3]).replace('"', '').replace("'", '')
    city = str(b.split(',')[-2]).replace('"', '').replace("'", '')
    district = str(b.split(',')[-1].replace('\n', '')).replace('"', '').replace("'", '')
    f.close()

    data2 = {"source": {"book_key": book_key, "client_ip": client_ip,  # "from_third_app": false,
                        "item_sources": [{
                            "goods_id": goods_id, "kdt_session_id": kdt_session_id,
                            "page_source": "", "sku_id": sku_id}],
                        "kdt_session_id": kdt_session_id, "need_app_redirect": 'false', "order_from": "cart",
                        "order_type": 0, "platform": "mobile", "salesman": ""},
             "config": {"contains_unavailable_items": 'false', "receive_msg": 'true', "use_points": 'false',
                        "use_wxpay": 'false',
                        "buyer_msg": ""}, "items": [
            {"deliver_time": 0, "goods_id": goods_id, "num": order_number, "sku_id": sku_id, "ump_sku_id": 0}],
             "seller": {"kdt_id": kdt_id, "store_id": 0}, "ump": {"activities": [
            {"activity_id": 0, "activity_type": 0, "external_point_id": 0, "goods_id": goods_id, "points_price": 0,
             "sku_id": sku_id, "use_points": 'false'}], "coupon": {}}, "unavailable_items": [],
             "delivery": {"has_freight_insurance": 'false',
                          "address": {"address_detail": address, "area_code": "110101", "city": city,
                                      "country": "中国", "county": district, "is_default": 1, "province": province,
                                      "tel": phone, "user_name": name},
                          "express_type": "express", "express_type_choice": 0}}
    order_url = 'https://cashier.youzan.com/pay/wsctrade/order/buy/bill.json'
    response3 = requests.post(order_url, json=data2, headers=headers, verify=False)
    if 'order_no' in response3.text:
        order_sn = response3.json()['data']['order_no']
        prepay_id = response3.json()['data']['pre_payment_preparation']['prepay_id']
        cashier_salt = response3.json()['data']['pre_payment_preparation']['cashier_salt']
        cashier_sign = response3.json()['data']['pre_payment_preparation']['cashier_sign']
        partner_id = response3.json()['data']['pre_payment_preparation']['partner_id']
        pay_url = 'https://cashier.youzan.com/v2/pay/Preorder/pay.json'
        data3 = {
            "prepay_id": prepay_id,
            "cashier_salt": cashier_salt,
            "cashier_sign": cashier_sign,
            "partner_id": partner_id,
            "pay_tool": "ALIPAY_WAP"
        }
        response4 = requests.post(pay_url, data=data3, headers=headers, verify=False)
        if 'submit_data' in response4.text:
            submit_data = response4.json()['data']['pay_data']['submit_data']
            a = urllib.parse.urlencode(submit_data)
            pay_url = 'https://mclient.alipay.com/home/exterfaceAssign.htm?' + a
            return True, pay_url, order_sn
        else:
            return False, '获取支付链接错误', order_sn
    else:
        return False, '获取订单号错误', ''


"""有赞下单入口函数"""


def yz_main(pdduid, kdtsessionid, goods_url, amount, order_number):
    cookie = 'KDTSESSIONID={}'.format(kdtsessionid)
    amount_ = eval(str(amount))
    sku_id, kdt_id, goods_id = get_goods_id(goods_url, amount_, cookie, order_number)
    if '错误' in sku_id:
        return {'code': 0, 'msg': sku_id}

    is_ok, pay_url, order_sn = pay(sku_id, kdt_id, goods_id, order_number)
    if is_ok:
        logger.log('INFO', '订单:[{}]获取成功'.format(order_sn, pay_url), 'yz_spider', pdduid)
        return {'code': 1, 'pay_url': pay_url, 'order_sn': order_sn, 'msg': '', 'goods_id': goods_id, 'sku_id': sku_id}
    else:
        return {'code': 0, 'pay_url': '', 'order_sn': order_sn, 'msg': pay_url, 'goods_id': goods_id}


if __name__ == '__main__':
    goods_url = 'https://h5.youzan.com/v2/goods/3ne9s2dat34vm'
    amount = 0.01
    order_number = 1
    kdtsessionid = "YZ486867746525601792YZZQdXT2BH"
    pdduid = 15113213321
    a = yz_main(pdduid, kdtsessionid, goods_url, amount, order_number)
    print(a)

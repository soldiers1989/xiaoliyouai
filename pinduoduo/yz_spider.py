# -*- coding:utf-8 -*-
__author__ = '张全亮'
import requests
import re
import urllib3
urllib3.disable_warnings()
import json
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
    "Cookie": "DO_CHECK_YOU_VERSION=1; KDTSESSIONID=YZ486867746525601792YZZQdXT2BH; yz_log_ftime=1536119919259; yz_log_uuid=07f21bb3-26dc-1c10-4f69-8e570dabd529;"
              " nobody_sign=YZ486867746525601792YZZQdXT2BH; yz_log_seqb=1536542782523; css_base=e76619006e57e80; css_base_wxd=499f4d24535c97b;"
              " css_goods=f5cf1178edc126b; css_buyer=e5d58de420ec4cd; css_new_order=b5dbb4d1e3747a9; css_trade=59d2eee6054e60e; "
              "css_showcase=b9109f0eebd342d; css_showcase_admin=cd9beb13ba6b79e; _canwebp=1; Hm_lvt_679ede9eb28bacfc763976b10973577b=1536542841;"
              " Hm_lpvt_679ede9eb28bacfc763976b10973577b=1536568833; _kdt_id_=40693930; yz_ep_view_track=ZzgrEE33nIOyI3mv2rFRLA%3D%3D;"
              " yz_ep_page_type_track=iDJ3GNJDHbhHtOl6W3j3ZA%3D%3D; yz_log_seqn=599"
}

""" 获取添加购物车需要的商品信息, 并对金额做判断"""
def get_goods_id(url, amount):
    response = requests.get(url, headers=headers, verify=False)
    html = response.text
    try:
        goods_list = re.findall('"list":.(.*?)]', html, re.I | re.S)
        price_list = re.findall('"price":(.*?),', str(goods_list), re.I | re.S)
        sku_id_list = re.findall('"id":(.*?),', str(goods_list), re.I | re.S)
        kdt_id_list = re.findall('"kdt_id":(.*?),', str(goods_list), re.I | re.S)
        goods_id_list = re.findall('goods_id":(.*?)},', str(goods_list), re.I | re.S)
    except:
        print('提取商品列表异常')
        return
    amount = str(amount) + '00'
    if amount not in price_list:
        print('订单金额不一致, 给定金额:{}'.format(amount[:-2]))
    for i in range(len(price_list)):
        if float(amount) == float(price_list[i]):
            sku_id = sku_id_list[i]
            kdt_id = kdt_id_list[i]
            goods_id = goods_id_list[0]
            return sku_id, kdt_id, goods_id
        else:
            continue


def add_shop_cart(sku_id, kdt_id, goods_id, goods_number):
    url = 'https://h5.youzan.com/v2/trade/cart/goods.jsonp?kdt_id={}&goods_id={}&postage=0&num={}&activity_id=0' \
               '&activity_type=0&sku_id={}&use_wxpay=0&callback=jsonp1'.format(kdt_id, goods_id, goods_number, sku_id)
    response2 = requests.get(url, headers=headers, verify=False)
    if 'success' in response2.text:
        return True
    else:

        return False


def main(url, amount, goods_number):
    sku_id, kdt_id, goods_id = get_goods_id(url, amount)
    print(sku_id, kdt_id, goods_id )
    if add_shop_cart(sku_id, kdt_id, goods_id, goods_number):
        pay(sku_id, kdt_id, goods_id, goods_number)
    else:
        print('添加商品信息失败！！！')


def pay(sku_id, kdt_id, goods_id, goods_number):
    url = 'https://h5.youzan.com/v2/trade/common/cache.json'
    data = {
        "common": {"activity_alias":[{"goods_id": goods_id,"sku_id":sku_id}],"order_from":"cart","kdt_id":kdt_id},
        "goodsList": [{"goods_id":goods_id,"sku_id":sku_id,"num":goods_number,"id": goods_id}],
        "isMultiShopChecked": 0
    }
    response = requests.post(url, json=data, headers=headers, verify=False)
    buy_url = response.json()['data']['buyUrl']
    print(buy_url)
    book_key = response.json()['data']['key']
    response2 = requests.get(buy_url, headers=headers, verify=False)
    client_ip = re.findall('"client_ip":"(.*?)",', response2.text)[0]


    data ={"source": {"book_key": book_key, "client_ip": "183.14.30.69", "from_third_app": false,
                "item_sources": [{
                                     "biz_trace_point_ext": "{\"st\":\"js\",\"sv\":\"0.4.9\",\"yai\":\"wsc_c\",\"uuid\":\"07f21bb3-26dc-1c10-4f69-8e570dabd529\",\"platform\":\"h5\",\"biz\":\"wsc\",\"client\":\"\"}",
                                     "cart_create_time": 1536573104, "cart_update_time": 1536573104,
                                     "goods_id": 417917220, "kdt_session_id": "YZ486867746525601792YZZQdXT2BH",
                                     "page_source": "", "sku_id": 36196920}],
                "kdt_session_id": "YZ486867746525601792YZZQdXT2BH", "need_app_redirect": false, "order_from": "cart",
                "order_type": 0, "platform": "mobile", "salesman": "",
                "user_agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
                "fromThirdApp": false},
     "config": {"contains_unavailable_items": false, "receive_msg": true, "use_points": false, "use_wxpay": false,
                "buyer_msg": ""}, "items": [
        {"deliver_time": 0, "goods_id": 417917220, "num": 2, "price": 2500, "sku_id": 36196920, "ump_sku_id": 0}],
     "seller": {"kdt_id": 40693930, "store_id": 0}, "ump": {"activities": [
        {"activity_id": 0, "activity_type": 0, "external_point_id": 0, "goods_id": 417917220, "points_price": 0,
         "sku_id": 36196920, "use_points": false}], "coupon": {}}, "unavailable_items": [],
     "delivery": {"has_freight_insurance": false,
                  "address": {"address_detail": "12楼", "area_code": "110101", "city": "北京市", "community": "",
                              "country": "中国", "country_type": 1, "county": "东城区", "id": 127545822, "is_default": 0,
                              "lat": "39.934442272263", "lon": "116.42282166241", "postal_code": "", "province": "北京市",
                              "tel": "15132123321", "user_id": 961217741, "user_name": "zs", "address_id": 127545822},
                  "express_type": "express", "express_type_choice": 0}}


if __name__ == '__main__':
    url = 'https://h5.youzan.com/v2/goods/2oe5y9jhz8z22?reft=1536561556985_1536561748067&spm=f71977761_ag40693930'
    amount = 25
    goods_number = 2
    main(url, amount, goods_number)
    sku_id, kdt_id, goods_id = 36196920, 40693930, 417917220
    pay(sku_id, kdt_id, goods_id, goods_number)
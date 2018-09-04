# -*- coding:utf-8 -*-
__author__ = '张全亮'
import urllib3
urllib3.disable_warnings()
import requests
from multiprocessing.dummy import Pool
from mysql_db import db_insert

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
    "accesstoken": "KMLVPRLG4U5L5CGMCH545HGPGRBZTVE3XS3N4NWINFF25DJWR42Q101a825"
}



def main():
    response = requests.get('https://api.pinduoduo.com/api/galen/v2/regions/1?pdduid=4336079679912', headers=headers,
                            verify=False)
    res_list = response.json()['regions']
    # pool = Pool(processes=20)
    for res_ in res_list:
    #     pool.apply_async(city, (res_['region_id'], res_['region_name']))
    #     # break
    # pool.close()
    # pool.join()
        city(res_['region_id'], res_['region_name'])


import datetime
def city(province_id, province):
    # print(111, province, province_id)
    url = 'https://api.pinduoduo.com/api/galen/v2/regions/{}?pdduid=4336079679912'.format(province_id)
    res = requests.get(url, headers=headers, verify=False)
    # print(22, res.json())
    for rse in res.json()['regions']:
        city_id = rse['region_id']
        city = rse['region_name']
        url2 = 'https://api.pinduoduo.com/api/galen/v2/regions/{}?pdduid=4336079679912'.format(city_id)
        res2 = requests.get(url2, verify=False, headers=headers)
        # print(res2.json())
        for rse2 in res2.json()['regions']:
            district_id = rse2['region_id']
            district = rse2['region_name']
            print(province, province_id, city, city_id, district, district_id)
            create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "insert into pdd_address(province, province_id, city, city_id, district, district_id, create_time)" \
                  " values ('{}', '{}','{}', '{}', '{}', '{}', '{}')".format(province, province_id, city, city_id, district, district_id, create_time)
            db_insert(sql)


if __name__ == '__main__':
    main()
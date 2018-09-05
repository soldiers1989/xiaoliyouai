import json, pymysql
from DBUtils.PooledDB import PooledDB

with open('config.json', 'r', encoding='utf-8') as f:
    mysql_config = json.loads(f.read())['mysql']
pool = PooledDB(pymysql, mincached=5, host=mysql_config['host'], user=mysql_config['username'],
                password=mysql_config['pwd'], database=mysql_config['db'], charset='utf8')
from logger import Logger

logger = Logger()


# 数据库插入，更新
def db_insert(sql):
    conn = pool.connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        logger.log("INFO", "数据插入, 更新", "mysql", "Admin")
    except Exception as ex:
        logger.log("ERROR", "数据插入, 更新错误, 原因:{}".format(ex), "mysql", "Admin")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# 数据库查询，返回查询结果
def db_query(sql):
    conn = pool.connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
    except Exception as ex:
        logger.log("ERROR", "数据查询错误, 原因: {}".format(ex), "mysql", "Admin")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    import datetime

    yesterday = datetime.date.today() + datetime.timedelta(-1)
    sql = 'select * from t_acc_order'
    a = db_query(sql)
    print(len(a))

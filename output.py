from redis_queue import RedisQueue
import time
import json
import threading


def say_hello(result):
    print('1', result, time.strftime("%c"))


q = RedisQueue('rq')
while 1:
    result = q.get_nowait()
    if not result:
        break
    time.sleep(2)

from redis_queue import RedisQueue
import time
from multiprocessing.dummy import Pool


q = RedisQueue('rq')  # 新建队列名为rq
pool = Pool(processes=100)
for i in range(1000):
    pool.apply(q.put, [i])
    print("input.py: data {} enqueue {}".format(i, time.strftime("%c")))
pool.close()
pool.join()
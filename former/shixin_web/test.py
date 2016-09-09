#coding=utf-8
from threadpool import ThreadPool,makeRequests
import threadpool
import json

def hello(m, n, o):
    """"""
    print "m = %s, n = %s, o = %s"%(m, n, o)

def run():
   # 方法1
    lst_vars_1 = ['1', '2', '3']
    lst_vars_2 = ['4', '5', '6']
    func_var = [(lst_vars_1, None), (lst_vars_2, None)]
    print func_var
    # 方法2
    dict_vars_1 = {'m':'1', 'n':'2', 'o':'3'}
    dict_vars_2 = {'m':'4', 'n':'5', 'o':'6'}
    func_var = [(None, dict_vars_1), (None, dict_vars_2)]

    pool = threadpool.ThreadPool(2)
    requests = threadpool.makeRequests(hello, func_var)
    [pool.putRequest(req) for req in requests]
    pool.wait()



def testJson():

    import json
    con = dict(id=(11,12))
    with open('lost_id.json','a') as f:
        f.write(json.dumps(con)+'\n')

    #
    # with open('shixin_start.json','r') as f:
    #     print json.loads(f.read())['id']


def lookGetResponse_content():
    import  requests
    url = 'http://shixin.court.gov.cn/image.jsp?date=Wed%20Aug%' \
          '2010%202016%2010:04:53%20GMT+0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
    proxies = {'http':'127.0.0.1:8888','https':'127.0.0.1:8888'}
    response = requests.get(url,timeout=5,proxies=proxies,)
    print 'hi'



def splitGroups(seq, step):

    index = 0
    seq_len =  len(seq)
    groups = []

    while index < seq_len:

        if index+step < seq_len:
            groups.append(seq[index:index+step])
        else:
            groups.append(seq[index:seq_len])
        index += step

    return groups

# end


def idQueue(start_id, goal=20, step=5):
    '''  构造协程请求的id序列
    :start_id: 开始id
    :goal: 将爬取的总数
    :step: 构造协程“并发”数
    :return: list, example: [[1,50], [50,100]...]
    '''
    if start_id < 0 or goal < 0 or step < 0 or goal < step :
        raise ValueError

    start_id = int(start_id)
    id_queue = [(start_id+i*step, start_id+(i+1)*step) for i in range(goal/step)]
    id_queue if  not goal%step else id_queue.append((id_queue[-1][-1], start_id+goal))
    return id_queue
    # end


# print idQueue(1,2,5)


class Mo(object):  # 可以自主调用init
    def __init__(self):
        self.header = dict()

    def changeHeader(self, info):
        self.header.update(info)




def test_insert():
    import time
    import pymongo
    from pymongo.errors import ServerSelectionTimeoutError

    conn = pymongo.MongoClient()
    db =  conn.test_db
    t_insert_one = db.t_insert_one
    t_insert_many = db.t_insert_many

    items = [dict(id=i) for i in range(1,10)]
    items_len = len(items)

    # t_begin = time.time()
    #
    # for item in items:
    #     t_insert_one.insert(item)
    # print 'inset_one 插入{0}条记录用时：{1}'.format(items_len, time.time()-t_begin)
    # # >> inset_one 插入999999条记录用时：185.820000172

    t_begin = time.time()
    try:
        t_insert_many.insert_many(items)
        print 'inset_one 插入{0}条记录用时：{1}'.format(items_len, time.time()-t_begin)
    except ServerSelectionTimeoutError:
        print 'silasilade '
    # inset_one 插入999999条记录用时：13.5699999332
    time.sleep(100)
    conn.close()
# end


def readJsonfromtxt(file='read_json_txt.txt'):

    with open(file,'r') as f:
        for line in f:
            yield json.loads(line)['id']

    # end


#
# if __name__ == '__main__':
#     for i in readJsonfromtxt():
#         print i

# 时间格式化为字符串
# from time import strftime,localtime
#
# with open(strftime('%Y-%m-%d.%H-%M',localtime())+'.txt','a') as f:
#     f.write('hello')

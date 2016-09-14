#coding=utf-8

import sys
reload(sys)
sys.path.append('../')
sys.setdefaultencoding('utf-8')


import os, json
import random, time

import gevent
import pymongo
import requests
from pytesser import *
from requests.exceptions import *
from requests.utils import dict_from_cookiejar
from gevent import monkey; monkey.patch_all()
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from public.share_func import userAgent, basicRequest, saveImage, recogSimpleImage, clawLog, getIp
from additional.mysql_process import queryRequestFailedID, updateRequestFailedID,\
    t_errUnknownQuery, t_errUnknownUpdate, getLostIDS


class ShiXinSpider(object):
    '''失信人记录spider'''

    conn = pymongo.MongoClient()
    spider_db = conn.spider
    t_shixin_person = spider_db.t_shixin_person
    t_shixin_company = spider_db.t_shixin_company
    t_shixin_err_timeout = spider_db.t_shixin_err_timeout
    t_shixin_err_unknown = spider_db.t_shixin_err_unknown


    def __init__(self):

        self.headers = {
            'Referer': '',
            'X-Forwarded-For': getIp(),
            'User-Agent': userAgent(),
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'shixin.court.gov.cn',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',

        }

        self.cookies = dict()


        self.threshold = 3                  # 验证码重拉次数
        self.err_timeout_items = list()     # 保存timeout的id
        self.err_unknown_items = list()     # 保存很有可能不存在的id

        self.shixin_person_items = list()   # 保存个人失信记录
        self.shixin_company_items = list()  # 保存公司失信记录

    # end


    def updateCookies(self):
        ''' 获取验证码流程（嵌套函数）
        :return:
        '''

        def visitSys():
            ''' 填充cookies
            :return: getSessionID()/False
            '''
            url = 'http://shixin.court.gov.cn/'
            options = {'method': 'get', 'url':url, 'headers': self.headers}

            response = basicRequest(options)
            if response:
                self.cookies.update(dict_from_cookiejar(response.cookies))
                # invoke next process
                return getSessionID()
            else:
                return False
        # def

        def getSessionID():
            ''' 填充cookies
            :return: getONEAPM_AI()/False
            '''
            url = 'http://shixin.court.gov.cn/image.jsp'
            self.headers['Referer'] = 'http://shixin.court.gov.cn/'
            options = {'method': 'get', 'url': url, 'cookies': self.cookies, 'headers': self.headers}

            response = basicRequest(options)
            if response:
                self.cookies.update(dict_from_cookiejar(response.cookies))
                #invoke next process
                return getONEAPM_AI()
            else:
                return False
        # def

        def getONEAPM_AI():
            ''' 填充cookies
            :return: getONEAPM_AI()/False
            '''
            params = {'functionId':'1'}
            url = 'http://shixin.court.gov.cn/visit.do'
            self.headers['Referer'] = 'http://shixin.court.gov.cn/'
            options = {'method': 'get', 'url': url, 'cookies': self.cookies, 'headers': self.headers}

            response = basicRequest(options)
            if response:
                self.cookies.update(dict_from_cookiejar(response.cookies))
                return self.cookies
            else:
                return False
        # def

        return visitSys()

    # end updateCookies


    def getCode(self):
        ''' 请求并保存验证码图片然后调用识别函数
        :return: 识别结果/None
         '''

        result = time.ctime().split()
        url =   'http://shixin.court.gov.cn/image.jsp?' \
                'date={0}%20{1}%20{2}%20{3}%20{4}%20GMT' \
                '+0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'\
                .format(result[0],result[1],result[2],result[4],result[3])

        self.headers['Accept'] = 'image/webp,image/*,*/*;q=0.8'
        self.headers['Referer'] = 'http://shixin.court.gov.cn/'
        options = {'method': 'get', 'url': url, 'cookies': self.cookies, 'headers': self.headers}

        response = basicRequest(options)
        if response and len(response.text):

            self.cookies.update(dict_from_cookiejar(response.cookies))
            # 以13位的时间戳来保存图片,默认路径为当前目录下的code文件夹
            image_path = saveImage(response)
            pw_code = recogSimpleImage(image_path)
            try:
                os.unlink(image_path)
            except WindowsError:
                pass
            if pw_code:
                self.threshold = 3                  # 将默认值还原
                return pw_code
            else:
                time.sleep(random.uniform(0, 1))    # 识别错误重拉
                return self.getCode()
        else:
            self.threshold -= 1
            time.sleep(random.uniform(1, 2))
            return self.getCode() if self.threshold > 0 else False
    # end getCode


    def getJson(self, sys_id, pw_code):
        '''  获得最后的json信息
        :param pw_code: 验证码
        :return: None
        '''
        params = {'id':'3780758','pCode':'5646'}
        params['id'] = sys_id
        params['pCode'] = pw_code

        url = 'http://shixin.court.gov.cn/findDetai'
        self.headers['Referer'] = 'http://shixin.court.gov.cn/'

        try:
            # 注意timeout的设置
            # proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}
            response = requests.get(url, params=params, cookies=self.cookies, headers=self.headers, timeout=5)
        except Timeout  as time_err:
            self.err_timeout_items.append(dict(sys_id=sys_id, err=str(time_err)))

        except (ConnectionError,HTTPError,RequestException) as other_err:
            self.err_unknown_items.append(dict(sys_id=sys_id, err= str(other_err)))

        else:
            # 注意判断条件 len(response.text) > 0 表示不为空
            if response.status_code not in (520,500) and len(response.text):
                try:
                    item = json.loads(response.text, encoding='utf-8')
                except (ValueError,Exception) as err_unknown:
                    self.err_unknown_items.append(dict(sys_id=sys_id, err=str(err_unknown)))
                else:
                    if 'businessEntity' in item.keys():
                        self.shixin_company_items.append(item)

                    elif 'sexy' in item.keys():
                        self.shixin_person_items.append(item)

                    else:
                        self.err_unknown_items.append(dict(sys_id=sys_id, err= str(item)))
            else:
                self.err_unknown_items.append(dict(sys_id=sys_id, err = 'http response code:{0}'.format(response.status_code)))

    # end getJson


    def startSpider(self, groups):
        '''  完成组队列请求json结果
        :param groups: [[],[],[]....] 或 [(),(),()...]
        :return: 返回因网络原因无法请求的所有组
        '''

        # t_begin = time.time()

        err_groups = list()
        cookies = self.updateCookies()

        if not cookies:
            print u'{0} :危险:请切换ip'.format(time.ctime())
            return groups

        for group in groups:
            code = self.getCode()
            if not code:
                err_groups.append(group); continue

            time.sleep(random.uniform(0, 1))    # 中断

            objs = list()
            if isinstance(group, tuple):
                for sys_id in range(group[0], group[1]):
                    objs.append(gevent.spawn(self.getJson, sys_id, code))
            else:
                for sys_id in group:
                    objs.append(gevent.spawn(self.getJson, sys_id, code))

            gevent.joinall(objs)

        return err_groups
        # print u'组完成：完成组{0},总用时：{1}'.format(groups, time.time()-t_begin)

    # end startSpider


    def saveItems(self):
        '''  保存数据到mongodb
        :return: None
        '''
        person = len(self.shixin_person_items)
        company = len(self.shixin_company_items)
        err_timeout = len(self.err_timeout_items)
        err_unknown = len(self.err_unknown_items)

        # 如有爬去到相应内容才建立连接
        if person:
            ShiXinSpider.t_shixin_person.insert_many(self.shixin_person_items)

        if company:
            ShiXinSpider.t_shixin_company.insert_many(self.shixin_company_items)

        if err_timeout:
            ShiXinSpider.t_shixin_err_timeout.insert_many(self.err_timeout_items)

        if err_unknown:
            ShiXinSpider.t_shixin_err_unknown.insert_many(self.err_unknown_items)

        return u'完成入库：个人信息{0}，公司信息{1}，超时信息{2}，错误信息{3}'.format(person, company, err_timeout, err_unknown)

    # end saveItems


    @staticmethod
    def idQueue(start_id, goal=10000, step=50):
        '''  构造协程请求的id序列
        :start_id: 开始id
        :goal: 将爬取的总数
        :step: 构造协程“并发”数
        :return: 队列, example: [[1,50], [50,100]...]
        '''
        if start_id < 0 or goal < 0 or step < 0 or goal < step :
            raise ValueError

        start_id = int(start_id)
        id_queue = [(start_id+i*step, start_id+(i+1)*step) for i in range(goal/step)]
        id_queue if not goal%step else id_queue.append((id_queue[-1][-1], start_id+goal))

        return id_queue

    # end idQueue


    @staticmethod
    def splitGroups(seq, step):
        '''划分相同cookie下要处理的大组'''

        index = 0
        seq_len =  len(seq)

        while index < seq_len:
            if index+step < seq_len:
                yield seq[index:index+step]
            else:
                yield seq[index:seq_len]
            index += step

    # end splitGroups


    @staticmethod
    def readGroups(file='shixin_groups_fail.txt'):
        groups = []
        with open(file,'r') as f:
            for line in f:
                groups.append(json.loads(line)['id'])
        return groups


    @staticmethod
    def getStartID():
        '''json文件读取启动id'''

        with open('shixin_start.json', 'r') as f:
                return json.loads(f.read())['id']

    # end getStartID

# end class


def groupsFailedAPI(file, num=4):
    '''  从文件中读出请求失败的组，并进行爬取
    :param file: 制定文件
    :param num: 每大组中小组个数
    :step: 小组中的id总数
    :return: None
    :example : groupsFailedAPI('./err_group/err_file.txt', 6)
    '''
    spider = ShiXinSpider()

    group_seq = spider.readGroups(file)

    t_begin = time.time()
    print u'Bingo：时间:{0}, 分组来源:{1}'.format(time.ctime(), file)

    for groups in spider.splitGroups(group_seq, num):

        spider.__init__()
        err_groups = spider.startSpider(groups)
        result = spider.saveItems()
        clawLog(groups, result)

        # 将遇到网络错误分组保存
        if err_groups:
            with open('shixin_lost.json', 'a') as f:
                for err_group in err_groups:
                    f.write(json.dumps(dict(id=err_group)) + '\n')

        time.sleep(random.uniform(0,1))
    # for

    # 解除DB连接
    ShiXinSpider.conn.close()

    print u'进程结束：总用时为{0}'.format(time.time() - t_begin)

# end



def errTimeoutAPI(num):
    '''从DB批量读取timeout表的sys_id,并进行请求
    :param num: 每次读取的id最大数
    :return: None
    :有效id:1741386
    '''

    t_begin = time.time()
    print u'Bingo：时间:{0}'.format(time.ctime())

    spider = ShiXinSpider()
    id_seq = queryRequestFailedID(num)

    while id_seq:
        for group in spider.splitGroups(id_seq, step=50):
            spider.__init__()
            err_groups = spider.startSpider([group])  # 注意传入参数为[group]
            result = spider.saveItems()
            clawLog(group, result)

            # 不出错代表全正确,更新数据库
            if not err_groups:
                updateRequestFailedID(group)

            time.sleep(random.uniform(0,1))
            id_seq = queryRequestFailedID(num)  # 继续读库
    # while

    # 解除DB连接
    ShiXinSpider.conn.close()

    print u'进程结束：总用时为{0}'.format(time.time() - t_begin)

# end


def errUnknownAPI(num):
    '''从DB批量读取unknwon表的sys_id,并进行请求
    :param num: 每次读取的id最大数
    :return: None
    :有效id:1741386
    '''
    t_begin = time.time()
    print u'Bingo：时间:{0}'.format(time.ctime())

    spider = ShiXinSpider()
    id_seq = t_errUnknownQuery(num)

    while id_seq:
        for group in spider.splitGroups(id_seq, step=50):
            spider.__init__()
            err_groups = spider.startSpider([group])  # 注意传入参数为[group]
            result = spider.saveItems()
            clawLog(group, result)

            # 不出错代表全正确,更新数据库
            if not err_groups:
                t_errUnknownUpdate(group)

            time.sleep(random.uniform(0,1))
            id_seq = t_errUnknownQuery(num)     # 继续读库

    # 解除DB连接
    ShiXinSpider.conn.close()

    print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
# end



def errLostIds():
    '''根据已经遍历的id求出有哪些id是丢失的，并进行请求
    :return: None
    :有效id:1741386
    '''
    t_begin = time.time()
    print u'Bingo：时间:{0}'.format(time.ctime())

    spider = ShiXinSpider()
    id_seq = getLostIDS()

    for group in spider.splitGroups(id_seq, step=50):
        spider.__init__()
        err_groups = spider.startSpider([group])  # 注意传入参数为[group]
        result = spider.saveItems()
        clawLog(group, result)

        # 将遇到网络错误分组保存
        if err_groups:
            with open('shixin_lost.json', 'a') as f:
                for err_group in err_groups:
                    f.write(json.dumps(dict(id=err_group)) + '\n')

        time.sleep(random.uniform(0,1))
    # for

    # 解除DB连接
    ShiXinSpider.conn.close()

    print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
# end


if __name__ == '__main__':
    pass
    # errUnknownAPI(2000)








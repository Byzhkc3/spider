#coding=utf-8

"""一个验证码的有效期为30秒，
每个验证码下该发多少个请求？每个cookies下应该重复多少次？
# 版本：V4
# 目标：可用版本
# 修改：拉验证码用同之前的cookies直接更新，同个cookies完成多个组
# 备注：网络好的情况可以适当添加大组的的小组数量 """

import sys
reload(sys)
sys.path.append('../')
sys.setdefaultencoding('utf-8')
import random
import gevent
import requests
import os, json, time

from requests.exceptions import *
from requests.utils import dict_from_cookiejar
from gevent import monkey; monkey.patch_all()

from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from public.share_func import *
from public.insert_dicts import insertDicts
from additional.mysql_process import *
from configuration.column_cfg import invalid_columns, valid_columns, valid_keys


class ShiXinSpider(object):
    """失信被执行人信息"""
    def __init__(self):

        self.headers = {
            'Referer': '',
            'User-Agent': userAgent(),
            'X-Forwarded-For': getIp(),
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'shixin.court.gov.cn',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',

        }
        self.cookies = dict()

        self.threshold = 3              # 验证码重拉次数
        self.valid_items = list()       # 有效id
        self.invalid_items = list()     # 无效/出错id
        self.dire_temp = os.path.join(os.getcwd(), 'temp')  # 临时图片目录
        self.dire_code = os.path.join(os.getcwd(), 'code')  # 验证码目录
    # end


    def updateCookies(self):
        """ 获取验证码流程（嵌套函数）
        :return:cookies obj/False """
        def visitSys():
            """ 填充cookies
            :return: getSessionID()/False """
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
            """填充cookies
            :return: getONEAPM_AI()/False
            """
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
            """ 填充cookies
            :return: getONEAPM_AI()/False
            """
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
        """ 请求并保存验证码图片然后调用识别函数
        :return: 识别结果/None """
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
            pw_code = recogImage(image_path, self.dire_temp)
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

    def saveErrID(self, sys_id, err_type):
        """:param sys_id: 单个id或者list,tuple
        :param err_type:
        :return:None """
        if err_type not in (1, 2, 3):
            raise ValueError('错误类型范围不在定义范围'.decode('utf-8'))

        if isinstance(sys_id, (list, tuple)):
            for i in sys_id:
                self.invalid_items.append(dict(sys_id = i, err_type = err_type))
        else:
            self.invalid_items.append(dict(sys_id = sys_id, err_type = err_type))
    # end


    def getJson(self, sys_id, pw_code):
        """  获得sys_id对应的信息
        :param pw_code: 验证码
        :return: None """
        params = {'id':sys_id, 'pCode':pw_code}
        url = 'http://shixin.court.gov.cn/findDetai'
        self.headers['Referer'] = 'http://shixin.court.gov.cn/'

        try:
            # 注意timeout的设置
            # proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}
            response = requests.get(url, params=params, cookies=self.cookies, headers=self.headers, timeout=10)
        except Timeout:
            self.saveErrID(sys_id, 2)
        except (ConnectionError,HTTPError,RequestException):
            self.saveErrID(sys_id, 3)
        else:
            if response.status_code not in (520, 500) and len(response.text):
                try:
                    item = json.loads(response.text, encoding='utf-8')
                except (ValueError, Exception):
                    self.saveErrID(sys_id, 3)
                else:
                    result = dict()
                    for i, v in enumerate(valid_keys):
                        result[valid_columns[i]] = item[v]
                    result['flag']  = 1 if 'businessEntity' in item.keys() else 0
                    self.valid_items.append(result)
            else:
                self.saveErrID(sys_id, 3)
    # end getJson


    def startSpider(self, groups):
        """  完成组队列请求json结果
        :param groups: 多个分组
        :return: None """
        cookies = self.updateCookies()

        if not cookies:
            print u'{0} :危险:请切换ip'.format(time.ctime())
            for group in  groups:
                self.saveErrID(group, 1)
                return

        for group in groups:
            code = self.getCode()
            if not code:
                self.saveErrID(group, 1)
                continue

            objs = list()
            for sys_id in range(group[0], group[1]):
                objs.append(gevent.spawn(self.getJson, sys_id, code))
            gevent.joinall(objs)
    # end startSpider


    def saveItems(self):
        """  保存数据到mysql
        :return: None """
        valid_num  = len(self.valid_items)
        invalid_num = len(self.invalid_items)

        if valid_num:
            table_name = 't_shixin_valid'
            insertDicts(table_name, valid_columns, self.valid_items)
        if invalid_num:
            table_name = 't_shixin_invalid'
            insertDicts(table_name, invalid_columns, self.invalid_items)

        return u'完成入库：有效信息{0}，错误信息{1}'.format(valid_num, invalid_num)
    # end saveItems


    def errUnknownSaveItems(self):
        """ 对可能不存在内容id再次遍历后数据的存储
        :return:None """
        valid_num  = len(self.valid_items)
        invalid_num = len(self.invalid_items)

        if valid_num:
            table_name = 't_shixin_valid'
            insertDicts(table_name, valid_columns, self.valid_items)
            deleteErrItems([item['sys_id'] for item in self.valid_items])
        if invalid_num:
            updateIDstatus([item['sys_id'] for item in self.invalid_items if item['err_type'] == 3])

        return u'完成入库：有效信息{0}，错误信息{1}'.format(valid_num, invalid_num)
    # end


    @staticmethod
    def idQueue(start_id, goal, step=50):
        """  构造协程请求的id序列
        :start_id: 开始id
        :goal: 将爬取的总数
        :step: 构造协程“并发”数
        :return: 队列, example: [[1,50], [50,100]...]
        """
        if start_id < 0 or goal < 0 or step < 0 or goal < step :
            raise ValueError
        start_id = int(start_id)
        id_queue = [(start_id+i*step, start_id+(i+1)*step) for i in range(goal/step)]
        id_queue if not goal%step else id_queue.append((id_queue[-1][-1], start_id+goal))
        return id_queue
    # end idQueue


    @staticmethod
    def splitGroups(seq, step):
        """ :param seq：list
        :param step: int
        :return:lsit
        """
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
    def getStartID():
        """json文件读取启动id"""
        with open('./configuration/shixin_start.json', 'r') as f:
                return json.loads(f.read())['sys_id']
    # end


    @staticmethod
    def saveClawedID(sys_id):
        with open('./configuration/shixin_start.json', 'w') as f:
            f.write(json.dumps(dict(sys_id=sys_id)))
    # end

# end class


def shixinSpiderAPI(goal, num=10, step=40):
    """ 遍历ID
    :param goal: 将要爬取数目
    :param num: 同一cookie下的小组数
    :step: 小组中的id总数(拿到验证码后"并发"的ID数)
    :return: None """
    makeDirs()
    spider = ShiXinSpider()
    start_id = spider.getStartID()
    groups_seq = spider.splitGroups(spider.idQueue(start_id, goal, step), num)

    for groups in groups_seq:
        t_begin = time.time()
        print u'Bingo：启动id:{0}, 目标数量:{1}'.format(start_id, goal)

        spider.__init__()
        spider.startSpider(groups)
        result = spider.saveItems()
        clawLog(groups, result)

        spider.saveClawedID(start_id+goal)
        removeAllFiles([spider.dire_code, spider.dire_temp])

        print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
# end


def errRequestFailAPI(num):
    """从DB批量读取表的sys_id,并进行请求
    :param num: 每次读取的id最大数
    :return: None
    :有效id:1741386 """
    makeDirs()
    spider = ShiXinSpider()
    id_seq = queryRequestFailID(num)

    while id_seq:
        for group in spider.splitGroups(id_seq, step=50):
            spider.__init__()
            t_begin = time.time()
            print u'Bingo：时间:{0}'.format(time.ctime())
            spider.startSpider([group])  # 注意传入参数为[group]
            result = spider.saveItems()
            clawLog(group, result)

            id_seq = queryRequestFailID(num)  # 继续读库
            removeAllFiles([spider.dire_code, spider.dire_temp])

            print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
    # while
# end


def errUnknownAPI(num):
    """从DB批量读取unknwon表的sys_id,并进行请求
    :param num: 每次读取的id最大数
    :return: None
    :有效id:1741386 """
    makeDirs()
    spider = ShiXinSpider()
    id_seq = queryErrUnknownID(num)

    while id_seq:
        for group in spider.splitGroups(id_seq, step=50):
            spider.__init__()
            t_begin = time.time()
            print u'Bingo：时间:{0}'.format(time.ctime())

            spider.startSpider([group])  # 注意传入参数为[group]
            result = spider.errUnknownSaveItems()
            clawLog(group, result)

            id_seq = queryErrUnknownID(num)
            removeAllFiles([spider.dire_code, spider.dire_temp])

            print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
# end


def errLostIDs():
    """ 根据已经遍历的id求出有哪些id是丢失的，并进行请求
    :return: None
    :有效id: 1741386 """
    makeDirs()
    spider = ShiXinSpider()
    id_seq = queryLostID(3307986, 4825018)

    for group in spider.splitGroups(id_seq, step=50):
        spider.__init__()
        t_begin = time.time()
        print u'Bingo：时间:{0}'.format(time.ctime())

        spider.startSpider([group])  # 注意传入参数为[group]
        result = spider.saveItems()
        clawLog(group, result)

        removeAllFiles([spider.dire_code, spider.dire_temp])
        print u'进程结束：总用时为{0}'.format(time.time() - t_begin)
    # for
# end


if __name__ == '__main__':
    num = 5
    step = 50
    goal = 1123
    shixinSpiderAPI(goal, num, step)




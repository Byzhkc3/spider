#coding=utf-8
import Image
import requests
import threading
import sys, random
import os, json, time

import shutil

reload(sys)
sys.path.append('../')
sys.setdefaultencoding('utf-8')

from requests.exceptions import *
from threadpool import makeRequests, ThreadPool
from requests.utils import dict_from_cookiejar
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from pytesser import image_to_string
from additional.mysql_process import insertDicts
from public.share_func import userAgent, basicRequest, saveImage, getIp, getTimestamp




class ZhiXingSpider(object):
    '''被执行人记录'''

    invalid_columns = ('sys_id', 'err_type')
    valid_columns = ('sys_id', 'name', 'card_num','case_code','reg_date','court_name','execute_money')
    json_keys  = ('id', 'pname', 'partyCardNum', 'caseCode','caseCreateTime', 'execCourtName', 'execMoney')

    def __init__(self):

        self.headers = {
            'Referer': '',
            'User-Agent': userAgent(),
            'Connection': 'keep-alive',
            'Host': 'zhixing.court.gov.cn',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'X-Forwarded-For': getIp(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        self.err_ids = list()
        self.threads_cookies = dict()

        self.valid_items = list()               # 成功记录
        self.invalid_items = list()             # 识别记录
        self.temp = os.path.join(os.getcwd(), 'temp')
    # end


    def getCookies(self):
        ''' 获取cookies流程（嵌套函数）
        :return: dict/False
        '''
        cookies = dict()

        def visitSys():
            ''' 填充cookies
            :return: getSessionID()/False
            '''
            url = 'http://zhixing.court.gov.cn/search/'
            options = {'method':'get', 'url':url, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                cookies.update(dict_from_cookiejar(response.cookies))
                # invoke next process
                return getSessionID()
            else:
                return False
        # def

        def getSessionID():
            ''' 填充cookies
            :return: getONEAPM_AI()/None
            '''

            url_one = 'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?87'
            url_two = 'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?3'
            self.headers['Referer'] = 'http://zhixing.court.gov.cn/'
            options_one = {'method':'get', 'url':url_one, 'cookies':cookies, 'headers':self.headers}
            options_two = {'method':'get', 'url':url_two, 'cookies':cookies, 'headers':self.headers}

            response = basicRequest(options_two) if basicRequest(options_one) else False

            if response:
                cookies.update(dict_from_cookiejar(response.cookies))
                #invoke next process
                return cookies
            else:
                return False

        # def

        return visitSys()
    # getCookies


    def getCode(self, re_num=3):
        ''' 请求并保存验证码图片然后调用识别函数
        :return: 识别结果/None
         '''
        threadID = threading.current_thread().ident
        cookies = self.threads_cookies[threadID]

        url =  'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?15'

        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'
        options = {'method':'get', 'url':url,
                   'cookies':cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response and len(response.text):
            image_path = saveImage(response, name=threadID)
            pw_code = self.recogImage(image_path, threadID)
            try:
                os.unlink(image_path)
            except WindowsError:
                pass
            if pw_code:
                return pw_code
            else:
                time.sleep(random.uniform(0, 1))    # 识别错误重拉
                return self.getCode( re_num) if re_num > 0 else False
        else:
            re_num -= 1
            time.sleep(random.uniform(0, 1))
            return self.getCode(re_num) if re_num > 0 else False
    # end getCode


    def recogImage(self, image_path, threadID):
        ''' 识别
        :param image_path: 图片路径
        :return: 数字字符串/False
        '''
        temp_img_name = getTimestamp() + str(threadID) + '.bmp'
        temp_txt_name = getTimestamp() + str(threadID)
        scratch_image_name = os.path.join(self.temp, temp_img_name)
        scratch_text_name_root = os.path.join(self.temp, temp_txt_name)
        try:
            img = Image.open(image_path).convert('L')
            result = image_to_string(img, scratch_image_name, scratch_text_name_root).strip()
            result = result if result.isdigit() else False
            return result
        except (IOError,Exception):
            del img
            return False
        finally:
            ZhiXingSpider.perform_cleanup(scratch_image_name, scratch_text_name_root)
    # end recogImage


    @staticmethod
    def perform_cleanup(scratch_image_name, scratch_text_name_root):
        """Clean up temporary files from disk"""   #  "tesseract.log"
        for name in (scratch_image_name, scratch_text_name_root + '.txt'):
            try:
                os.unlink(name)
            except OSError:
                pass

    def getJson(self, sys_id):
        '''  获得最后的json信息
        :param pw_code: 验证码
        :return: None
        '''

        threadID = threading.current_thread().ident
        if not threadID in self.threads_cookies.keys():
            cookies = self.getCookies()
            if cookies:
                self.threads_cookies[threadID] = cookies
            else:
                self.saveErrID(sys_id, 1); return

        pw_code = self.getCode()
        if not pw_code:
            self.saveErrID(sys_id, 1); return


        params = {'id':sys_id, 'j_captcha':pw_code}
        url = 'http://zhixing.court.gov.cn/search/newdetail'
        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'

        try:
            # 注意timeout的设置
            # proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}
            response = requests.get(url, params=params, cookies=self.threads_cookies[threadID],
                                     headers=self.headers, timeout=2)
        except Timeout:
            self.saveErrID(sys_id, 2)

        except (ConnectionError,HTTPError,RequestException):
            self.saveErrID(sys_id, 3)

        else:
            # 注意判断条件 len(response.text) > 0 表示不为空
            if len(response.text) > 10:
                try:
                    item = json.loads(response.text, encoding='utf-8')
                except (ValueError,Exception):
                    self.saveErrID(sys_id, 3)
                else:
                    result = dict()
                    for i,v in enumerate(ZhiXingSpider.json_keys):
                        result[ZhiXingSpider.valid_columns[i]] = item[v]
                    self.valid_items.append(result)
            else:
                self.saveErrID(sys_id, 3)
    # end getJson


    def saveErrID(self, sys_id, err_type):

        if err_type not in (1,2,3):
            raise ValueError

        err_item = dict(sys_id=sys_id,err_type=err_type)
        self.invalid_items.append(err_item)
    # end


    def saveItems(self):
        '''  保存数据到mongodb
        :return: None
        '''
        valid_num  = len(self.valid_items)
        invalid_num = len(self.invalid_items)

        if valid_num:
            table_name = 't_zhixing_valid'
            insertDicts(table_name, self.valid_columns, self.valid_items)
        if invalid_num:
            table_name = 't_zhixing_invalid'
            insertDicts(table_name, self.invalid_columns, self.invalid_items)

        return u'完成入库：有效信息{0}，错误信息{1}'.format(valid_num, invalid_num)

    # end saveItems



    @staticmethod
    def clawLog(groups, result, file_name):
        '''
        :param groups: 组
        :return: None
        '''
        dire = './clawed_log'
        if not os.path.exists(dire):
            os.mkdir(dire)

        path = os.path.join(dire, file_name)
        with open(path, 'a') as f:
            f.write(time.ctime() + ':\t' + result + '\n' +  json.dumps(dict(id=groups)) + '\n'*2)
    # end clawLog


    @staticmethod
    def idQueue(start_id, goal=10000, step=50):
        '''
        :start_id: 开始id
        :goal: 将爬取的总数
        :step: 单个线程任务
        :return: 队列, example: [[1,50], [50,100]...]
        '''
        if start_id < 0 or goal < 0 or step < 0:
            raise ValueError

        start_id = int(start_id)
        id_queue = [[start_id+i*step, start_id+(i+1)*step] for i in range(goal/step)]
        id_queue if not goal%step else id_queue.append([id_queue[-1][-1], goal])

        return id_queue

    # end idQueue


    @staticmethod
    def getStartID():
        '''json文件读取启动id'''
        with open('./configuration/zhixing_start.json','r') as f:
                return json.loads(f.read())['id']

    # end getStartID


# class


def zhixingSpiderAPI(goal, thread_num=1):
    '''
    :param goal: 将要爬取id数目
    :param thread_num: 线程数目
    :return: None
    '''
    temp = 'D:\\run_now\\zhixing_web\\temp'
    code = 'D:\\run_now\\zhixing_web\\code'

    spider = ZhiXingSpider()
    pool = ThreadPool(thread_num)

    for i in range(840):

        t_begin = time.time()
        spider.__init__()

        start_id = spider.getStartID()
        print time.ctime() + u'\tBegin：启动id:{0}, 目标数量:{1}'.format(start_id, goal)

        id_queue = range(start_id, start_id+goal+1)
        requests = makeRequests(spider.getJson, id_queue)
        [pool.putRequest(req) for req in requests]
        pool.wait()

        result = spider.saveItems()
        log_id = list()
        log_id.extend([id_queue[0],id_queue[-1]])
        spider.clawLog(log_id, result, 'zhixin_log.log')

        with open('./configuration/zhixing_start.json','w') as f:
            f.write(json.dumps(dict(id=start_id+goal)))

        print time.ctime() + u'\tOver：finish it,coast:{0} \n'.format(time.time()-t_begin)

        # 删除文件
        for file in os.listdir(code):
            try:
                os.remove(os.path.join(code, file))
            except Exception:

                pass
        for file in os.listdir(temp):
            try:
                os.unlink(os.path.join(temp, file))
            except Exception as ex :
                print ex
                pass


if __name__ == '__main__':
    zhixingSpiderAPI(2500, thread_num=50)









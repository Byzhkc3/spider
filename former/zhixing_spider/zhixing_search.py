#coding=utf-8
import os
import re
import json
import time
import random
import sys
reload(sys)
sys.path.append('../')
import threading
from math import ceil
from lxml import etree
from requests.utils import dict_from_cookiejar
from threadpool import ThreadPool, makeRequests
# from public.insert_dicts import insertDicts
from public.share_func import basicRequest, \
    userAgent, getIp, recogImage, clawLog, makeDirs
from zhixing_spider.configuration.column_cfg import valid_keys, invalid_columns


class ZhiXingSpider(object):
    """根据身份证号/企业号查询执行信息"""

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
        self.id_seq = list()
        self.threads_cookies = dict()   # 线程字典

        self.valid_items = list()       # 有效id
        self.invalid_items = list()     # 无效/出错id
    # end


    def getCookies(self):
        """ 获取cookies流程（嵌套函数）
        :return: dict/False """

        cookies = dict()

        def visitSys():
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
            url_one = 'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?87'
            url_two = 'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?3'
            self.headers['Referer'] = 'http://zhixing.court.gov.cn/'
            options_one = {'method':'get', 'url':url_one, 'cookies':cookies, 'headers':self.headers}

            response =  basicRequest(options_one)
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
        """ 获得验证码
        :return: int/False """

        threadID = threading.current_thread().ident
        if not threadID in self.threads_cookies.keys():
            cookies = self.getCookies()
            if cookies:
                self.threads_cookies[threadID] = cookies
            else:
                return
        cookies = self.threads_cookies[threadID]

        url =  'http://zhixing.court.gov.cn/search/security/jcaptcha.jpg?' + str(random.randint(0,99))

        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'
        options = {'method':'get', 'url':url,
                   'cookies':cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response and len(response.text):
            cookies.update(dict_from_cookiejar(response.cookies))
            pw_code = recogImage(response.content)
            if pw_code:
                return pw_code
            else:
                # time.sleep(random.uniform(0, 1))    # 识别错误重拉
                return self.getCode( re_num) if re_num > 0 else False
        else:
            re_num -= 1
            # time.sleep(random.uniform(0, 1))
            return self.getCode(re_num) if re_num > 0 else False
    # end getCode


    def searchByCardNum(self, name, card_num, re_num=3):
        """ 通过身份证号/公司号查记录
        :return: 页总数 """

        threadID = threading.current_thread().ident
        if not threadID in self.threads_cookies.keys():
            cookies = self.getCookies()
            if cookies:
                self.threads_cookies[threadID] = cookies
            else:
                return
        cookies = self.threads_cookies[threadID]

        self.card_num = card_num
        self.name = name

        pw_code = self.getCode()
        if not pw_code:
            re_num -= 1
            return self.searchByCardNum(name, card_num, re_num) if re_num > 0 else False

        form = {
            'searchCourtName':'全国法院（包含地方各级法院）',
            'selectCourtId':'1',
            'selectCourtArrange':'1',
            'pname':'',
            'cardNum':'68087331-4',
            'j_captcha':'68965'
        }
        form['j_captcha'] = pw_code
        form['cardNum'] = card_num
        form['pname'] = name

        url = 'http://zhixing.court.gov.cn/search/newsearch'
        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies':cookies, 'headers':self.headers}

        response = basicRequest(options, resend_times=0)
        if response:
            checkout = self.checkOut(response.text)
            if not checkout:
                re_num -= 1
                return self.searchByCardNum(name, card_num, re_num)if re_num > 0 else False
            else:
                page_num = 0
                selector = etree.HTML(response.text)
                text = selector.xpath('//div[@id="ResultlistBlock"]/div/text()')
                text = ''.join(text).replace('\n','').replace('\t','').encode('utf-8')
                tr_num = int(re.search('共(\d+)', text).group(1))
                if tr_num > 0:
                    page_num = int(ceil((tr_num)/10.0))
                    sys_ids = self.findIDs(selector)
                    self.id_seq.extend(sys_ids)

                return page_num
    # end


    def findIDs(self, selector):

        trs = selector.xpath('//table[@id="Resultlist"]/tbody/tr')[1:]
        return [tr.xpath('td[5]/a/@id')[0] for tr in trs]
    # end


    def changePage(self, page_i, re_num=3):

        threadID = threading.current_thread().ident
        if not threadID in self.threads_cookies.keys():
            cookies = self.getCookies()
            if cookies:
                self.threads_cookies[threadID] = cookies
            else:
                return

        pw_code = self.getCode()
        if not pw_code:
            re_num -= 1
            return self.changePage(page_i, re_num) if re_num > 0 else False

        form = {
            'currentPage':'2',
            'selectCourtId':'1',
            'selectCourtArrange':'1',
            'pname':'',
            'cardNum':'68087331-4'
        }
        form['currentPage'] = page_i
        form['cardNum'] = self.card_num
        form['pname'] = self.name

        url = 'http://zhixing.court.gov.cn/search/newsearch?j_captcha=' + pw_code
        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies': self.threads_cookies[threadID], 'headers':self.headers}

        response = basicRequest(options, resend_times=0)
        if response:
            checkout = self.checkOut(response.text)
            if not checkout:
                re_num -= 1
                return self.changePage(page_i, re_num) if re_num > 0 else False
            else:
                selector = etree.HTML(response.text)
                sys_ids = self.findIDs(selector)
                self.id_seq.extend(sys_ids)
        else:
            re_num -= 1
            return self.changePage(page_i, re_num) if re_num > 0 else False

    # end

    def checkOut(self, text):
        """ 通过页面返回内容检查验证码是否出错,
        正确返回True,否则返回False
        :param text:response.text
        :return:True/False """

        selector = etree.HTML(text)
        title = selector.xpath('//title/text()')[0]
        checkout = re.match('验证码出现错误', title.encode('utf-8'))
        # if checkout:
        #     print checkout.group()
        return False if checkout else True


    def saveErrID(self, sys_id, err_type):
        """ 保存出错的id,和对应的错误类型
        1位请求错误/2为超时/3为未知错误
        :param sys_id: id
        :param err_type: 1/2/3
        :return: None """

        if err_type not in (1,2,3):
            raise ValueError
        err_item = dict(sys_id=sys_id,err_type=err_type)
        self.invalid_items.append(err_item)
        return False
    # end


    def getJson(self, sys_id, re_num=4):
        """  获得id对应的被执行信息（json格式）
        :param sys_id: id
        :return: None """

        threadID = threading.current_thread().ident
        if not threadID in self.threads_cookies.keys():
            cookies = self.getCookies()
            if cookies:
                self.threads_cookies[threadID] = cookies
            else:
                self.saveErrID(sys_id, 1); return
        cookies=self.threads_cookies[threadID]

        pw_code = self.getCode()
        if not pw_code:
            re_num -= 1
            return self.getJson(sys_id, re_num) if re_num > 0 else self.saveErrID(sys_id, 1)

        params = {'id':sys_id, 'j_captcha':pw_code}
        url = 'http://zhixing.court.gov.cn/search/newdetail'
        self.headers['Referer'] = 'http://zhixing.court.gov.cn/search/'
        options = {'method': 'get', 'params':params, 'url': url,
                   'cookies': cookies, 'headers': self.headers, 'timeout':1 }

        response = basicRequest(options, resend_times=0)
        if response and len(response.text) > 10:
            try:
                item = json.loads(response.text, encoding='utf-8')
            except (ValueError,Exception):
                self.saveErrID(sys_id, 3)
            else:
                result = dict()
                for k, v in item.items():
                    if k in valid_keys.keys():
                        key = valid_keys[k]
                        result[key] = v
                self.valid_items.append(result)
        else:
            re_num -= 1
            return self.getJson(sys_id, re_num) if re_num > 0 else self.saveErrID(sys_id, 3)

    # end getJson


    def saveItems(self):
        """  保存数据到mysql
        :return: None """

        # valid_columns = valid_keys.values()

        valid_num  = len(self.valid_items)
        invalid_num = len(self.invalid_items)

        # if valid_num:
        #     table_name = 't_zhixing_valid'
        #     insertDicts(table_name, valid_columns, self.valid_items)
        # if invalid_num:
        #     table_name = 't_zhixing_invalid'
        #     insertDicts(table_name, invalid_columns, self.invalid_items)

        return u'完成入库：有效信息{0}，错误信息{1}'.format(valid_num, invalid_num)
    # end saveItems

# class


def searchByCardNumAPI(name='', card_num='', thread_num=3):
    """ 根据身份证号/企业号查询接口
    :param card_num:身份证号/企业号
    :return: dict(valid=[], invalid=[]) / {} """

    makeDirs()
    if not name and not name:
        raise ValueError

    spider = ZhiXingSpider()
    page_num = spider.searchByCardNum(name, card_num)
    pool = ThreadPool(thread_num)
    try:
        if page_num > 1:
            requests = makeRequests(spider.changePage, range(2, page_num+1))
            [pool.putRequest(req) for req in requests]
            pool.wait()

        requests = makeRequests(spider.getJson, spider.id_seq)
        [pool.putRequest(req) for req in requests]
        pool.wait()
    except Exception:
        pass

    result = spider.saveItems()
    clawLog(spider.id_seq, result)

    return dict(valid=spider.valid_items, invalid=spider.invalid_items)
# end



if __name__ == '__main__':
    # demo
    print time.ctime() + ':\t' + 'Test start'

    t_begin = time.time()
    card_num = '77535404-X'
    name = '漳州伟翔精密机械有限公司'
    results = searchByCardNumAPI(name, card_num)

    cost_seconds = time.time()-t_begin
    print time.ctime() + ':\t' + 'Test over, cost: {0} seconds\n'.format(cost_seconds)

    print results


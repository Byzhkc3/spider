#coding=utf-8

"""
Goal：
    广东中国移动用户基本和通话记录的爬取和存储
Problem：
    1、通过selenium进行登录
Date:
    2016/7/28
Author:
    moyh
"""
from copy import copy

import sys
reload(sys)
sys.path.append('../')
sys.setdefaultencoding("utf-8")

import time,json,random,re
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import *

from three_operators.china_mobile.necessary.parse_json import parseCallJson
from three_operators.china_mobile.necessary.mobile_month import getMonthSeq
import three_operators.china_mobile.configuration.columns as config

try:
    from public import ConfigOperate, userAgent,\
        basicRequest,searchPhoneInfo,checkParamFormat
except ImportError as import_error:
    print import_error

_time_usual = 10
_time_special = 60

class ChinaMobile_GD(object):
    """中国移动-广东爬虫"""
    def __init__(self, phone_attr):
        self.__headers = {
            'Accept': '*/*',
            'User-Agent': userAgent(),
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN',
            'Connection': 'keep-alive',
        }
        self.browser = None
        self.cookies = dict()   # cookies
        self.phone_attr = phone_attr # 手机属性
        self.user_items = list()   # 用户信息
        self.call_items = list()   # 通话信息
    # end

    @staticmethod
    def getCookies(cookies_seq):
        cookie_dict = dict()
        if cookies_seq:
            for cookie in cookies_seq:
                cookie_dict[cookie['name']] = cookie['value']

        return cookie_dict
    # end

    @staticmethod
    def timeSleep(min=1, max=3):
        if min <= max:
            return time.sleep(random.uniform(min, max))
        else:
            raise ValueError('param value error')
    # end

    def getCode(self):

        url = 'http://gd.10086.cn/my/REALTIME_LIST_SEARCH.shtml'
        browser = webdriver.Chrome()
        browser.get(url)
        browser.implicitly_wait(_time_usual)  # open the login page
        ChinaMobile_GD.timeSleep()
        try:
            browser.switch_to.frame('iframe_login_pop')
        except NoSuchFrameException as frame_ex:
            print frame_ex
            sys.exit(0)
        else:
            user_name_element = browser.find_element_by_id('mobile')  # 用户名框
            user_name_element.clear()
            user_name_element.send_keys(self.phone_attr['phone'])
            browser.find_element_by_id('btn_get_dpw').click()
            self.browser = browser # 注意保存browser
            print u'hi,动态验证码已经发送到手机:' + self.phone_attr['phone']
            return 2000
    # def

    def login(self):

        user_name_element = self.browser.find_element_by_id('mobile')  # 用户名框
        password_element = self.browser.find_element_by_name('password')  # 密码框
        dynamic_pw_element = self.browser.find_element_by_name('dynamicCaptcha')  # 动态密码框
        login_element = self.browser.find_element_by_id('loginSubmit')  # 登录按钮

        user_name_element.clear()
        user_name_element.send_keys(self.phone_attr['phone'])

        password_element.clear()
        password_element.send_keys(self.phone_attr['password'])

        dynamic_pw_element.send_keys(self.phone_attr['phone_pwd'])
        login_element.click()  # login after click
        self.browser.implicitly_wait(_time_usual)
        ChinaMobile_GD.timeSleep(2, 3)
        return self.judgeLogin()  # 登陆态判断
    # def

    def judgeLogin(self):
        """ 进行登录判断
        :return:
        """
        def getErrorByMatch(pattern, string):  # 通过match错误原因来判断是否存在错误
            try:
                re.match(pattern, string).group(1)
            except (IndexError, AttributeError):
                return False
            else:
                return True
        # def
        try:
            tips = self.browser.find_element_by_xpath('//span[@class="text"]').text.strip()
        except (NoSuchElementException, WebDriverException):
            return 2000
        else:
            if getErrorByMatch(r'密码', tips):
                print 'pw error'
                return 4401  # 密码错误
            elif getErrorByMatch(r'动态密码', tips):
                return 4402  # 动态码错误
            else:
                raise Exception(u'未知错误')
    # def

    def clawAllInfo(self):
        try:
            self.browser.find_element_by_xpath('//div[@id="mathBox"]/div/a[1]').click()  # 点击查询
            self.browser.implicitly_wait(_time_usual)
        except NoSuchElementException as ex:
            return 4000
        self.cookies = self.getCookies(self.browser.get_cookies())     # cookies更新
        if len(self.cookies) > 0:
            self.clawUserInfo()  # 爬取用户信息
            self.clawCallInfo()  # 爬去通话记录
            return 2000
        else:
            return 4000
    # end

    def clawUserInfo(self):
        """Get the basic information of the user
        :return:False/list
        """
        def queryInfo():
            form = {'servCode': 'MY_BASICINFO'}
            url = 'http://gd.10086.cn/commodity/servicio/track/servicioDcstrack/query.jsps'
            self.__headers['Referer'] = 'http://gd.10086.cn/my/myService/myBasicInfo.shtml'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                return getInfo()
            else:
                return False
        # def

        def getInfo():
            form = {'servCode':'MY_BASICINFO', 'operaType':'QUERY'}
            url = 'http://gd.10086.cn/commodity/servicio/servicioForwarding/queryData.jsps'
            self.__headers['Referer'] = 'http://gd.10086.cn/my/myService/myBasicInfo.shtml'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.cookies, 'timeout':30, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                return clawInfo(response.text)
            else:
                return False
        # def

        def clawInfo(text):
            try:
                selector = etree.HTML(text)
                table = selector.xpath('//table[@class="tb02"]')[0]
                values =  table.xpath('tbody/tr[2]/td/text()')
                if len(values) == 0:
                    values =  table.xpath('tr[2]/td/text()')
                item = dict(
                    phone = values[0],
                    name = values[1],
                    cert_num = values[2],
                    open_date = values[4],
                    company = self.phone_attr['company'],
                    province = self.phone_attr['province'],
                    city = self.phone_attr['city']
                )
                # 填充字段
                [item.setdefault(i, '') for i in config.COLUMN_USER]
                self.user_items.append(item) # 保存记录
            except (IndexError,Exception) as ex:
                return 4000
        # def
        return queryInfo()
    # end

    def clawCallInfo(self):
        """ Save all call records
        :return: null
        """
        item = {
            'cert_num': self.user_items[0]['cert_num'],
            'phone': self.user_items[0]['phone']
        }
        text_seq = self.getFiveMonthCall()
        if len(text_seq) > 0:
            for text in text_seq:
                results = json.loads(text)['content']['realtimeListSearchRspBean']['calldetail']['calldetaillist']
                for record in results:
                    temp = copy(item)
                    # 'place', 'time', 'time', 'chargefee','period', 'contnum', 'becall', 'conttype'
                    for k, v in record.items():
                        if k in config.KEY_CONVERT_CALL.keys():
                                column_name = config.KEY_CONVERT_CALL[k]
                                temp[column_name] = v
                        try:
                            self.convertValues(temp)  # 入库修正
                        except Exception as ex:
                            print ex,
                            for k,v in temp.items():
                                print k, v
                    self.call_items.append(temp)
        else:
            print 'call records not found'
    # end


    def convertValues(self,item):
        key = item.keys()

        if 'call_type' in key:
            call_type = {u'主叫': 1, u'被叫': 2 }
            if item['call_type'] in call_type.keys():
                item['call_type'] = call_type[item['call_type']]
            else:
                item['call_type'] = 3

        if 'land_type'in key:
            land_type = {u'本地': 1, u'国内长途': 2}
            if item['land_type'] in land_type.keys():
                item['land_type'] = land_type[item['land_type']]
            else:
                item['land_type'] = 3

        if 'call_date' in key:
             # '04-01 11:18:50' 对时间进行分割
            temp =  item['call_date'].split(' ')
            item['call_date'] = '2016-' + temp[0]
            item['call_time'] = temp[1]
    # end

    def getFiveMonthCall(self):
        """Get the call records of the past five months
        :return: list (maybe empty)
        """
        text_seq = list()
        month_seq = getMonthSeq()[1:2]

        for month in month_seq:
            print '请耐心等待,正在查询{0}:'.format(month)
            result = self.getMonthCall(month)
            if result:
                text_seq.append(result)
            else:
                print '抱歉,查询{0}月通话数据失败'.format(month)
        # for
        return text_seq
    # end

    def getMonthCall(self,month):
        """Get the call records according to month
        :param month: year+month, example:'201602'
        :return: False/response.text
        """
        def getUniqueTag():
            form = {'month': '201602'}
            form['month'] = month
            url = 'http://gd.10086.cn/commodity/servicio/nostandardserv/realtimeListSearch/query.jsps'
            self.__headers['Referer'] = 'http://gd.10086.cn/my/REALTIME_LIST_SEARCH.shtml?dt=1469030400000'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                try:
                    unique_tag = json.loads(response.text)['attachment'][0]['value']
                    return getMonthRecords(unique_tag)
                except (KeyError,IndexError,Exception) as ex :
                    print 'unique_tag not found, error:',ex
                    return False
            else:
                return False
        # def

        def getMonthRecords(unique_tag):

            form = dict(uniqueTag='20160721164253242', monthListType='0')
            form['uniqueTag'] = unique_tag

            url = 'http://gd.10086.cn/commodity/servicio/nostandardserv/realtimeListSearch/ajaxRealQuery.jsps'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.cookies, 'timeout':20, 'headers':self.__headers}   # pay attention to "timeout"

            response = basicRequest(options)
            if response:
                return response.text
            else:
                return False
        # def
        return getUniqueTag()
    # end
# class


# 获取手机动态码
def getNoteCode(phone_attr):
    """
    :param phone_attr: {'phone':'15802027662', 'province':'广东', 'city':'广州', 'company':2}
    :return:
    """
    if not isinstance(phone_attr, dict):
        raise ValueError(u'参数错误')

    spider = ChinaMobile_GD(phone_attr)
    result = spider.getCode()
    if result == 2000:
        return dict(code=2000, temp=spider) # 成功
    else:
        return dict(code=4444, temp=None) # 失败


# 更新手机动态码
def updateNoteCode():
    pass


# 登陆系统
def loginSys(spider):

    if not isinstance(spider, ChinaMobile_GD):
        raise ValueError(u'参数错误')

    login = spider.login()
    if login == 2000: # 登录成功
        search = spider.clawAllInfo() # 爬取内容
        if search == 2000:
            result=dict(
                t_operator_user = spider.user_items,
                t_operator_call = spider.call_items
            )
            return dict(code=2000, result=result)
    else:
        return dict(code=login, temp=None) # 密码错误4401,动态码错误4402



if __name__ == '__main__':

    from three_operators.necessary.phone_attr import getAttributes

    phone_attr = getAttributes('15802027662')
    if phone_attr:

        phone_attr['password'] = '20168888'  # 添加密码
        code_result = getNoteCode(phone_attr) # 获得手机动态码

        if code_result['code'] == 2000:
            print u'获得手机动态码成功'
            # 获得手机动态码，并调用登陆
            code_result['temp'].phone_attr['phone_pwd'] = raw_input(u'请输入手机动态码:')

            login_result = loginSys(code_result['temp'])
            if login_result['code'] == 2000:
                result = login_result['result']
                print result
            else:
                print login_result
        else:
            print code_result



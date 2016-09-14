#coding=utf-8

'''
Goal：
    广东中国移动用户基本和通话记录的爬取和存储
Problem：
    1、通过selenium进行登录，速度慢
Date:
    2016/7/28
Author:
    moyh
'''

import sys
reload(sys)
sys.path.append('../')
sys.setdefaultencoding("utf-8")

import time,json,random,re

from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import *

from parse_json import parseCallJson
from mobile_month import getMonthSeq
from mobile_sql import t_china_mobile_user_insert,\
    t_china_mobile_call_insert
try:
    from public import ConfigOperate, userAgent,\
        basicRequest,searchPhoneInfo,checkParamFormat
except ImportError as import_error:
    print import_error


class GD_ChinaMobile(object):
    '''user info of China Mobile'''

    time_wait_usual = 10
    time_wait_special = 60

    def __init__(self):
        self.__headers = {
            'Accept': '*/*',
            'User-Agent': None,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN',
            'Connection': 'keep-alive',
        }
        self.__cookies = None
        self.__headers['User-Agent'] = userAgent()

        self.id_and_phone = None
        self.__threshold = 3    # 系统繁忙，重新请求阈值
        self.__section = ConfigOperate('person_mobile.cfg').getDict('Moyh')
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


    def loginSys(self, login_code=None):
        '''
        :return:
        '''

        def loginStart(url=None):

            url = 'http://gd.10086.cn/my/REALTIME_LIST_SEARCH.shtml'
            browser = webdriver.Chrome()
            browser.get(url)
            browser.implicitly_wait(GD_ChinaMobile.time_wait_usual)   # open the login page
            GD_ChinaMobile.timeSleep()
            try:
                browser.switch_to.frame('iframe_login_pop')
            except NoSuchFrameException as frame_ex:
                print frame_ex
                sys.exit(0)
            else:
                return loginSys(browser)


        def loginSys(browser):

            user_name_element = browser.find_element_by_id('mobile')        # 用户名框
            password_element = browser.find_element_by_name('password')     # 密码框
            dynamic_pw_element = browser.find_element_by_name('dynamicCaptcha')     # 动态密码框
            login_element = browser.find_element_by_id('loginSubmit')   # 登录按钮

            user_name_element.clear()
            user_name_element.send_keys(self.__section['user_name'])

            password_element.clear()
            password_element.send_keys(self.__section['password'])

            if login_code == None:
                browser.find_element_by_id('btn_get_dpw').click()
                print 'hi,动态验证码已经发送到手机:' + self.__section['user_name']
                return dict(result=200 ,error='had send password to you')
            else:
                dynamic_pw_element.send_keys(login_code)
                login_element.click()    # login after click
                browser.implicitly_wait(GD_ChinaMobile.time_wait_usual)
                GD_ChinaMobile.timeSleep(2,3)

                return judgeLogin(browser)
        # def


        def judgeLogin(browser):
            '''
            :param browser:
            :return:
            '''
            def getErrorByMatch(pattern, string):   # 通过match错误原因来判断是否存在错误
                try:
                    re.match(pattern,string).group(1)
                except (IndexError,AttributeError):
                    return False
                else:
                    return True
            # def

            try:
                tips = browser.find_element_by_xpath('//span[@class="text"]').text.strip()
            except (NoSuchElementException,WebDriverException):
                return dict(result=2000, browser=browser)
            else:
                if getErrorByMatch(r'密码',tips):
                    print 'pw error'
                    return dict(result=4401, error='密码出错')
                    # 输入并点击登录
                elif getErrorByMatch(r'动态密码', tips):
                    return dict(result=4402, error='动态码出错')
                    # 输入并点击登录
                else:
                    raise Exception('未知错误')
        # def

        return loginStart()
    # end


    def clawAllInfo(self, browser):
        try:
            browser.find_element_by_xpath('//div[@id="mathBox"]/div/a[1]').click()  # 点击查询
            browser.implicitly_wait(GD_ChinaMobile.time_wait_special)
        except NoSuchElementException as ex:
            print '定位查询图标失败',ex

        self.__cookies = self.getCookies(browser.get_cookies())     # cookies更新
        if len(self.__cookies) > 0:
            user = self.clawUserInfo()   # save user info
            call = self.clawCallInfo()   # save call info
            return dict(user=user, call=call)
        else:
            print 'nothing in cookies'
    # end


    def clawCallfromHtml(self):     # 提取selenium得到的查询页面
        pass
    # end


    def clawUserInfo(self):
        '''Get the basic information of the user
        :return:False/list
        '''

        def queryInfo():

            form = {'servCode':'MY_BASICINFO'}
            url = 'http://gd.10086.cn/commodity/servicio/track/servicioDcstrack/query.jsps'
            self.__headers['Referer'] = 'http://gd.10086.cn/my/myService/myBasicInfo.shtml'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.__cookies, 'headers':self.__headers}

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
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.__cookies, 'timeout':30, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                return clawInfo(response.text)
            else:
                return False
        # def

        def clawInfo(text):

            keys = ['phone', 'name', 'cert_id', 'puk_id', 'open_date']
            try:
                selector = etree.HTML(text)
                table = selector.xpath('//table[@class="tb02"]')[0]
                values =  table.xpath('tbody/tr[2]/td/text()')
                if len(values) == 0:
                    values =  table.xpath('tr[2]/td/text()')
                row = dict(zip(keys,values))
                row['end_date'] = table.xpath('tbody/tr[4]/td[4]/text()')[0]

                self.id_and_phone = [row['cert_id'], row['phone']]

                return [row['phone'], row['name'], row['cert_id'], row['puk_id'], row['open_date'], row['end_date']]

            except (IndexError,Exception) as ex:
                print 'parse html of the user info fail,ex:{0}'.format(ex)
                return False
        # def

        row =  queryInfo()
        return t_china_mobile_user_insert(row)
    # end


    def clawCallInfo(self):
        ''' Save all call records
        :return: null
        '''
        text_seq = self.getFiveMonthCall()
        if len(text_seq) > 0:
            rows = parseCallJson(text_seq, self.id_and_phone)
            return t_china_mobile_call_insert(rows)
        else:
            print 'call records not found'
    # end


    def getFiveMonthCall(self):
        '''Get the call records of the past five months
        :return: list (maybe empty)
        '''

        text_seq = list()
        month_seq = getMonthSeq()[1:]

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
        '''Get the call records according to month
        :param month: year+month, example:'201602'
        :return: False/response.text
        '''
        def getUniqueTag():

            form = {'month': '201602'}
            form['month'] = month

            url = 'http://gd.10086.cn/commodity/servicio/nostandardserv/realtimeListSearch/query.jsps'
            self.__headers['Referer'] = 'http://gd.10086.cn/my/REALTIME_LIST_SEARCH.shtml?dt=1469030400000'
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                try:
                    unique_tag = json.loads(response.text, encoding='utf8')['attachment'][0]['value']
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
            options = {'method':'post', 'url':url, 'form':form, 'cookies':self.__cookies, 'timeout':20, 'headers':self.__headers}   # pay attention to "timeout"

            response = basicRequest(options)
            if response:
                return response.text
            else:
                return False
        # def
        return getUniqueTag()
    # end

    def logoutSys(self):
        pass
    # end


    def startSpider(self, phone_num, password, login_code=None):
        '''
        :param phone_num: 手机号
        :param password: 密码
        :param login_code: 动态码[当为None是标记为首次访问,否则标记为输入的动态码]
        :return:
        '''
        self.__section['user_name'] = phone_num
        self.__section['password'] = password

        login_result = self.loginSys(login_code)

        if login_result['result'] == 2000:

            result = self.clawAllInfo(login_result['browser'])

            if result['call']['result'] == True and result['user']['result'] == True:
                return dict(result=2000)
            else:
                return dict(result=4444, error= result['call']['error'] + result['user']['error'])
        else:
            return login_result
    # end

# class


def apiGDChinaMobile(phone_num, password, login_code=None):  # GD china mobile api
    '''
    :param phone_num: 全为数字的字符串
    :param password: 全为数字的字符串(长度不少于6位)
    :return:
    '''
    check = checkParamFormat(phone_num, password)
    if check == True:
        demo = GD_ChinaMobile()
        result = demo.startSpider(phone_num, password,login_code)
        return result
    else:
        return check
# end






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
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from copy import copy
import time,json,random,re
from lxml import etree
import spider.public.db_config as DB
from selenium import webdriver
from selenium.common.exceptions import *
from spider.public import userAgent, basicRequest
from necessary.mobile_month import getMonthSeq
import configuration.columns as config
from selenium.webdriver import DesiredCapabilities

_time_wait = 2
_time_usual = 10
_time_special = 20

capabilities = DesiredCapabilities.PHANTOMJS.copy()
capabilities["phantomjs.page.settings.loadImages"] = False  # 禁止加载图片,默认加载
phantom_path = r'C:\driver\phantomjs-2.1.1-windows\bin\phantomjs.exe'

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
        self.cookies = dict()        # cookies
        self.browser = None
        self.phone_attr = phone_attr # 手机属性
        self.user_items = list()     # 用户信息
        self.call_items = list()     # 通话信息
        self.refresh_num = 3         # 更新峰值
    # end

    @staticmethod
    def timeSleep(min=1, max=3):
        # 设置中断
        if min <= max:
            return time.sleep(random.uniform(min, max))
        else:
            raise ValueError('param value error')
    # end

    @staticmethod
    def judgeByMatch(pattern, string):
         # 通过match内容来判断相关类型
        try:
            re.match(pattern, string).group(1)
        except (IndexError, AttributeError):
            return False
        else:
            return True
    # end

    def openBrowser(self):
        """打开广东移动官网首页"""
        url = 'http://gd.10086.cn/my/REALTIME_LIST_SEARCH.shtml'
        # self.browser = webdriver.PhantomJS(executable_path=phantom_path, desired_capabilities=capabilities)
        self.browser = webdriver.Chrome(r'C:\driver\chromedriver.exe')
        self.browser.get(url)
        self.browser.implicitly_wait(_time_usual)  # open the login page
        self.timeSleep()
        print u'打开浏览器'
        return True
    # end

    def switch_iframe(self):
        """跳转到登录框"""
        try:
            self.browser.switch_to.frame('iframe_login_pop')
            print u'已经跳转到登陆框'
        except NoSuchFrameException as frame_ex:
            print '无法跳转到登陆的iframe',frame_ex
            self.browser.close()
            sys.exit(0)
        try:
            self.click = self.browser.find_element_by_id('btn_get_dpw')
        except (NoSuchElementException, ElementNotVisibleException, WebDriverException) as ex:
            print u'btn_get_dpw元素定位异常'
            if self.refresh_num > 0:
                self.refresh_num -= 1
                self.browser.refresh()
                self.browser.implicitly_wait(_time_usual)
                return self.switch_iframe()  # 调用自身
            else:
                print u'跳转到登录框失败'
                return False
        else:
            return True
    # end

    def clickButton(self):
        """模拟点击获取手机动态密码, 然后关闭驱动"""
        try:
            user_name_element = self.browser.find_element_by_id('mobile')  # 手机号框
            # user_name_element.clear()
            user_name_element.send_keys(self.phone_attr['phone'])
            self.click.click()
        except (NoSuchElementException, WebDriverException) as ex:
            print u'模拟点击获取异常:', ex
            return False
        else:
            print u'已经发送动态密码，请查收'
            return True
        finally:
            self.browser.close()
    # end

    def login(self):
        """登录广东移动官网系统"""
        try:
            user_name_element = self.browser.find_element_by_id('mobile')  # 用户名框
            password_element = self.browser.find_element_by_name('password')  # 密码框
            dynamic_pw_element = self.browser.find_element_by_name('dynamicCaptcha')  # 动态密码框
            login_element = self.browser.find_element_by_id('loginSubmit')  # 登录按钮
        except (NoSuchElementException, WebDriverException) as ex:
            print u'登陆过程模拟定位失败',ex
            pass
        else:
            print u'登陆过程模拟定位成功'
            # 输入手机号码
            user_name_element.clear()
            user_name_element.send_keys(self.phone_attr['phone'])
            # 输入服务密码
            password_element.clear()
            password_element.send_keys(self.phone_attr['password'])
            # 输入动态密码
            dynamic_pw_element.send_keys(self.phone_attr['phone_pwd'])
            # # 点击登陆
            login_element.click()
            self.browser.implicitly_wait(_time_special)
            # 登陆态判断
            return self.judgeLogin()
    # end

    def judgeLogin(self):
        """判断登录的状态"""
        try:
            tips = self.browser.find_element_by_xpath('//span[@class="text"]').text.strip().encode('utf-8')
            print u'请观察登陆成功或者失败的tip:',tips
        except (NoSuchElementException, WebDriverException) as err:
            print u'无法定位登陆信息'
            return dict(code=2000, cookies=self.getLoginCookies(self.browser.get_cookies()))
        else:
            print u'在else里请观察登陆成功或者失败的tip:',tips
            if self.judgeByMatch('(密码)', tips):
                print 'pw error'
                return dict(code=4401, cookies=None)  # 密码错误
            elif self.judgeByMatch('(动态密码错误)', tips):
                return dict(code=4402, cookies=None)  # 动态码错误
            elif tips == '':
                print u'登陆成功,tips为空'
                cookies=self.getLoginCookies(self.browser.get_cookies())
                return dict(code=2000, cookies=cookies)
            else:
                raise Exception(u'未知错误')
    #end

    def getLoginCookies(self, driver_cookies):
        """ 获取登录后的cookies
        :param driver_cookies:
        :return:
        """
        if not isinstance(driver_cookies, list):
            print u'获取登录后的cookies失败'
        else:
            login_cookies = dict()
            for cookie in driver_cookies:
                # print 'key:' + cookie['name'] + '---->' + 'value:' + cookie['value']
                login_cookies[cookie['name']] = cookie['value']
            return login_cookies
    # end

    def saveCookies(self, cookies):
        self.cookies = cookies
    # end

    def getDynamicCode(self):
        """获取手机动态码逻辑函数"""
        print u'start-获得手机动态码'
        if self.openBrowser():
            if self.switch_iframe():
                return dict(code=2000) if self.clickButton() else dict(code=4000)
            else:
                return  dict(code=4000)
        else:
            return  dict(code=4000)
    # end

    def loginSys(self):
        """登录系统逻辑函数,登陆成功则返回cookie字典"""
        if self.openBrowser():
            if self.switch_iframe():
                result = self.login()
                if result['code'] == 2000:
                    return result
            else:
                pass
        else:
            pass
    # end

    def queryUserInfo(self):
        """查询用户信息-请求1"""
        form = {'servCode': 'MY_BASICINFO'}
        url = 'http://gd.10086.cn/commodity/servicio/' \
              'track/servicioDcstrack/query.jsps'
        self.__headers['Referer'] = 'http://gd.10086.cn/' \
                                    'my/myService/myBasicInfo.shtml'
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies':self.cookies, 'headers':self.__headers}
        response = basicRequest(options)
        return True if response else False
    # end

    def getUserInfo(self):
        """查询用户信息-请求2"""
        form = {'servCode':'MY_BASICINFO', 'operaType':'QUERY'}
        url = 'http://gd.10086.cn/commodity/servicio/' \
              'servicioForwarding/queryData.jsps'
        self.__headers['Referer'] = 'http://gd.10086.cn/' \
                                    'my/myService/myBasicInfo.shtml'
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies':self.cookies,'timeout':30, 'headers':self.__headers}
        response = basicRequest(options)
        return response.text if response else False
    # end

    def clawUserInfo(self, text):
        """解释页面内容,返回基本用户信息字典"""
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
            city = self.phone_attr['city'],
            user_valid = 1
        )
        # 填充字段,默认设置为''
        for i in config.COLUMN_USER:
            item.setdefault(i, '')
        return item
    # end

    def getUniqueTag(self, month):
        """获得月通话数据-请求1"""
        form = {'month': '201602'}
        form['month'] = month
        url = 'http://gd.10086.cn/commodity/servicio/' \
              'nostandardserv/realtimeListSearch/query.jsps'
        self.__headers['Referer'] = 'http://gd.10086.cn/my/' \
                                    'REALTIME_LIST_SEARCH.shtml?dt=1469030400000'
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies':self.cookies, 'headers':self.__headers}
        response = basicRequest(options)
        if response:
            try:
                unique_tag = json.loads(response.text)['attachment'][0]['value']
                return unique_tag
            except (KeyError,IndexError,ValueError, Exception) as ex :
                print 'unique_tag not found, error:',ex
                return False
        else:
            return False
    # end

    def getMonthText(self, unique_tag):
        """获得月通话数据-请求2"""
        form = dict(uniqueTag=unique_tag, monthListType='0')
        url = 'http://gd.10086.cn/commodity/servicio/' \
              'nostandardserv/realtimeListSearch/ajaxRealQuery.jsps'
        # pay attention to "timeout"
        options = {'method':'post', 'url':url, 'form':form,
                   'cookies':self.cookies, 'timeout':20, 'headers':self.__headers}
        response = basicRequest(options)
        return response.text if response else False
    # end

    def clawCallInfo(self, text):
        """解释页面内容,返回基本通话记录字典"""
        temp = {
            'cert_num': self.user_items[0]['cert_num'],
            'phone': self.user_items[0]['phone']
        }
        items = list() # 保存当月通话记录
        if len(text) > 0:
            results = json.loads(text)['content']['realtimeListSearchRspBean']['calldetail']['calldetaillist']
            for record in results:
                item = copy(temp)
                # key的转换
                # 'place', 'time', 'time', 'chargefee',
                # 'period', 'contnum', 'becall', 'conttype'
                for k, v in record.items():
                    if k in config.KEY_CONVERT_CALL.keys():
                            column_name = config.KEY_CONVERT_CALL[k]
                            item[column_name] = v
                self.convertValues(item)
                items.append(item)
        return items
    # end

    def convertValues(self,item):
        """temp为非空字典"""
        key = item.keys()
        # 呼叫类型(主叫1,被叫2,其他3)
        if 'call_type' in key:
            call_type = {u'主叫': 1, u'被叫': 2 }
            if item['call_type'] in call_type.keys():
                item['call_type'] = call_type[item['call_type']]
            else:
                item['call_type'] = 3
        # 通话类型(本地通话1,省内通话2,其他3)
        if 'land_type'in key:
            land_type = {u'本地': 1, u'国内长途': 2}
            if item['land_type'] in land_type.keys():
                item['land_type'] = land_type[item['land_type']]
            else:
                item['land_type'] = 3
        # 拆分为通话日期(年-月-日), 通话时间(时:分:秒)
        if 'call_date' in key:
            date_time =  item['call_date'].split(' ')
            item['call_date'] = '2016-' + date_time[0]
            item['call_time'] = date_time[1]
    # end

    def getMonthCalls(self, month):
        """Get the call records according to month
        :param month: year+month, example:'201602'
        :return:
        """
        unique_tag = self.getUniqueTag(month)
        if unique_tag:
            month_text = self.getMonthText(unique_tag)
            call_items = self.clawCallInfo(month_text)
            return call_items
        else:
            print u'请求月数据失败, unique_tag获取失败'
    # end

    def getUserItems(self):
        """逻辑实现-获得用户基本信息"""
        if self.queryUserInfo():
            text = self.getUserInfo()
            if text:
                item = self.clawUserInfo(text)
                self.user_items.append(item)
            else:
                print u'失败- 查询用户信息-请求2'
        else:
            print u'失败- 查询用户信息-请求1'
    # end

    def getCallItems(self):
        """逻辑实现-获得通话记录信息"""
        for month in getMonthSeq()[:1]:
            print '请耐心等待,正在查询{0}:'.format(month)
            items = self.getMonthCalls(month)
            print len(items)
    # end

    def saveItems(self):
        """保存数据到mysql"""
        valid_num = len(self.user_items)
        invalid_num = len(self.call_items)
        if valid_num:
            DB.insertDictList(config.TABEL_NAME_1, config.COLUMN_USER, self.user_items)
        if invalid_num:
            DB.insertDictList(config.TABLE_NAME_2, config.COLUMN_CALL, self.call_items)
        return u'完成入库：有效信息{0}，错误信息{1}'.format(valid_num, invalid_num)
    # end

# class


def getNoteCode():
    """获取手机动态码"""
    _phone_attr = {'phone':'15802027662', 'province':'广东',
                   'city':'广州', 'company':2, 'password':'20168888'}
    spider = ChinaMobile_GD(_phone_attr)
    result = spider.getDynamicCode()
    if result['code'] == 2000:
        return result   # dict(code=2000)
    else:
        return dict(code=4444, temp=None) # 失败
# end


def updateNoteCode():
    """更新手机动态码"""
    pass
# end

def loginSys():
    """登陆系统 并返回用户信息"""
    _phone_attr = {'phone':'15802027662', 'province':'广东',
                   'city':'广州', 'company':2, 'password':'20168888'}
    _phone_attr['phone_pwd'] = raw_input(u'请输入手机动态码:')
    spider = ChinaMobile_GD(_phone_attr)
    result  = spider.loginSys()   # 登陆成功返回cookies
    if result['code'] == 2000:
        spider.saveCookies(result['cookies'])
        spider.getUserItems()
        print spider.user_items
# end

if __name__ == '__main__':
    print 'start-ing'
    t_begin = time.time()
    result = getNoteCode()
    print u'获取验证码的时间为:',time.time()-t_begin
    t_begin = time.time()
    if result['code'] == 2000:
        loginSys()
    print u'登录系统的时间为:',time.time()-t_begin


#coding=utf-8

'''
版本:
    version 0.1
    整个流程通畅,请求-提取内容-存库。提供了外部调用了api。
问题:
    时间耗费高
备注:
    作为流程参考版
'''

import sys
import time

reload(sys)
sys.path.append('../')
sys.setdefaultencoding("utf-8")

import json,re,random
from requests.utils import dict_from_cookiejar

from three_operators.china_unicom.addtional.unicom_date import getDateSuq
from three_operators.china_unicom.addtional.parse_json import parseCallJson,parseUserJson
from three_operators.china_unicom.addtional.unicom_sql import t_china_unicom_call_insert,t_china_unicom_user_insert
try:
    from public import ConfigOperate, userAgent, basicRequest, checkParamFormat
except ImportError as import_error:
    print import_error



class PersonUnicom(object):
    '''user info of China Unicom'''


    def __init__(self):
        '''Initialization Parameters'''

        self.__headers = {
            'Accept': '*/*',
            'User-Agent': None,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.__cookies  = dict()
        self.__headers['User-Agent'] = userAgent()

        self.__threshold = 3    # 系统繁忙，重新请求阈值
        self.__section = ConfigOperate('person_unicom.cfg').getDict('Moyh')
    # end

    @staticmethod
    def getTimestamp(length=13):
        '''Get timestamp'''

        if isinstance(length,int) and length >= 10:
            temp = str(time.time()).split('.')
            temp = ''.join(temp)
            if len(temp) > length:
                return temp[0:length]
            else:
                return temp + '0'*(length-len(temp))
        else:
            raise TypeError('the type/value of param is wrong')
    # end

    def loginSys(self):
        '''Login process'''

        def visitSys():

            url = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'get', 'url':url, 'cookies':None, 'headers':self.__headers}

            response = basicRequest(options)
            if response: #
                return sysCheckLogin()
            else:
                return dict(result=4000, func='visitSys')
        # def

        def sysCheckLogin():
            '''Check login, if not return cookie dict(e3=XX,route=XX)'''

            url = 'http://iservice.10010.com/e3/static/check/checklogin/?_=' + self.getTimestamp()
            self.__headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':None, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                self.__cookies.update(dict_from_cookiejar(response.cookies))
                time.sleep(5)
                return loginByJS()
            else:
                return dict(result=4000, func='sysCheckLogin')
        # end

        def loginByJS():
            '''Login sys by HTTP GET,  return cookie dit(piw=XX, JUT=XX, _uop_id=XX) if login successfully '''

            params = {
                '_': '1468474921490',   # req_time + 1
                'callback': 'jQuery172000024585669494775475_1468770450339',
                'password': '662670',
                'productType': '01',
                'pwdType': '01',
                'redirectType':	'03',
                'redirectURL': 'http://www.10010.com',
                'rememberMe': '1',
                'req_time': '1468474921489',
                'userName':	'18617112670'
            }
            params['req_time'] = self.getTimestamp()
            params['_'] = str(int(params['req_time'])+1)
            params['userName'] = self.__section['user_name']
            params['password'] = self.__section['password']

            url = 'https://uac.10010.com/portal/Service/MallLogin'
            self.__headers['Referer'] = 'http://uac.10010.com/portal/hallLogin'
            options = {'method':'get', 'url':url, 'params':params, 'cookies':None, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                return judgeLogin(response)
            else:
                return dict(result=4000, func='loginByJS')
        # def

        def judgeLogin(response):

            try:
                code = re.search(r'resultCode:"(.*?)"', response.text).group(1)
            except (AttributeError,IndexError) as ex:
                return dict(result=4000, func='judgeLogin')
            else:
                if code == '0000':      # 登录成功
                    print 'loginSys finish'
                    self.__cookies.update(dict_from_cookiejar(response.cookies))
                    return dict(result=2000, error='no error' )

                elif code == '7007':    # 密码出错
                    print 'pw error'
                    return dict(result=4401, error='pw error')

                elif code == '7999':    # 系统繁忙
                    print 'sys busy'
                    time.sleep(random.uniform(1,3))
                    return loginByJS()

                elif code == '7072':    # 账号错误
                    print 'name error'
                    return dict(result=4400, error='user_name error')

                elif code == '7009':
                    print 'phone_num error'
                    return dict(result=4404, error= 'phone_num not exist')
                else:
                    raise Exception('未知错误')
        # def
        return visitSys()
    # end


    def clawUserInfo(self):

        def sysCheckLoginAgain():
            '''Check login to make sure you have login'''

            url = 'http://iservice.10010.com/e3/static/check/checklogin/?_=' + self.getTimestamp()
            self.__headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                return getHeaderView()
            else:
                return dict(result=4000, func='sysCheckLoginAgain')
        # def

        def getHeaderView():
            '''Claw header_view which contains balance(余额)/open_date(开户时间)/cert_id(证件号)'''

            url = 'http://iservice.10010.com/e3/static/query/headerView'
            self.__headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response: #
                part_info = getPartBasicInfo(response.text)
                return saveUserInfos(part_info)
            else:
                return dict(result=4000, func='getHeaderView')
        # def

        def getPartBasicInfo(text):
            '''Get user's a part of basic info '''

            part_info = dict()
            result = json.loads(text, encoding='utf-8')

            part_info['balance'] = result['result']['account']
            part_info['open_date'] = result['userinfo']['opendate']
            part_info['cert_id'] = result['userinfo']['certnum']
            part_info['home'] = getBelongPos()

            return part_info
        # def

        def getBelongPos():
            '''Get the home of mobile phone'''

            url = 'http://iservice.10010.com/e3/static/weather/city?_=' + self.getTimestamp()
            options = {'method':'post', 'url':url, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options,resend_times=0)
            if response:
                return response.text.strip()
            else:
                return dict(result=4000, func='getBelongPos')
        # def

        def saveUserInfos(part_info): #  cert_id, balance, open_date, home
            '''Claw and save user info'''

            params = { '_':'1468549625712', 'menuid':'000100030001'}

            params['_'] = self.getTimestamp()
            url = 'http://iservice.10010.com/e3/static/query/searchPerInfo/'
            self.__headers['Referer'] = 'http://iservice.10010.com/e3/query/personal_xx.html'
            options = {'method':'post', 'url':url, 'params':params, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                part_info.update(self.__section)
                user = parseUserJson(response.text, part_info)
                if user:
                    inser_user = t_china_unicom_user_insert(user)
                    return inser_user
                else:
                    return dict(result=5000, error='parseUserJson failed')
            else:
                return dict(result=4000, func='clawCallRecords')
        # def
        print 'start claw user info'
        return sysCheckLoginAgain()
    # end


    def clawCallInfo(self):

        def clawAllCallRecords():

            text_seq = list()
            date_seq = getDateSuq()

            for date_tuple in date_seq: # get month

                time.sleep(random.uniform(0,1))

                text = callRecordRequest(date_tuple)
                page_json = json.loads(text,encoding='utf8')
                if 'errorMessage' in page_json.keys():  # 存在错误
                    continue
                else:   # get page
                    text_seq.append(text)
                    total_record = int(page_json['totalRecord'])
                    remain_page = total_record / 100
                    if remain_page > 0:
                        i = 2
                        while i <= remain_page + 1:
                            time.sleep(random.uniform(0,1))
                            text_seq.append(callRecordRequest(date_tuple, page_no=i))
                            i += 1
                        # while
                    else:
                        continue
            # for
            return text_seq
        # def

        def callRecordRequest(date_tuple, page_no=1, resend = 2):  #完成单次请求[存在网络繁忙则重传]
            '''完成单次请求'''

            params = { '_':'1468549625712', 'menuid':'000100030001'}
            form = {'pageNo':'1', 'pageSize':'100', 'beginDate':'2016-07-01', 'endDate':'2016-07-18'}

            form['pageNo'] = page_no
            form['beginDate'] = date_tuple[0]
            form['endDate'] = date_tuple[1]
            params['_'] = self.getTimestamp()

            url = 'http://iservice.10010.com/e3/static/query/callDetail'
            self.__headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'form':form, 'params':params, 'cookies':self.__cookies, 'headers':self.__headers}

            response = basicRequest(options)
            if response:
                page_json = json.loads(response.text, encoding='utf8')
                if 'errorMessage' in page_json.keys() and  resend > 0 and page_json['errorMessage']['respCode'] == '4114030193': # 存在系统繁忙
                    return callRecordRequest(date_tuple, page_no, resend-1)     # 繁忙重传
                else:
                    return response.text
            else:
                return dict(result=4000, func='callRecordRequest')
        # def
        print 'start claw call info'
        text_seq = clawAllCallRecords()
        rows = parseCallJson(text_seq)
        return t_china_unicom_call_insert(rows)
    # end


    def logoutSys(self):
        '''logout without check'''

        url = 'http://iservice.10010.com/e3/static/common/logout?_=' + self.getTimestamp()
        options = {'method':'post', 'url':url, 'cookies':None, 'headers':self.__headers}

        response = basicRequest(options,resend_times=0)
        if response:
            return dict(result=2000)
        else:
            pass
    # end



    def startSpider(self, phone_num, password):
        '''
        流程: 登录(返回)-> 爬取用户信息（返回）-> 爬取用户通话记录（返回）-> 退出（返回）
        '''

        self.__section['user_name'] = phone_num
        self.__section['password'] = password

        login_result = self.loginSys()

        if login_result['result'] == 2000:
            user = self.clawUserInfo()     # 爬取用户信息
            call = self.clawCallInfo()     # 爬取通话记录
            if user['result'] == True and call['result'] == True:
                return dict(result=2000)
            else:
                return dict(result=4444, error= user['error'] + call['error'])
        else:
            return login_result
    # end

# class


def apiChinaUnicom(phone_num=None, password=None):  # API
    '''
    :param phone_num: 全为数字的字符串
    :param password: 全为数字的字符串(长度不少于6位)
    :return:
    '''
    check = checkParamFormat(phone_num, password)
    if check == True:
        time_start = time.time()
        demo = PersonUnicom()
        result = demo.startSpider(phone_num, password)
        print time.time() - time_start
        return result
    else:
        return check
# end
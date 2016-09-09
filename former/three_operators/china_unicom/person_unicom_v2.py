#coding=utf-8

import time
import json
import re
from math import ceil

import gevent
from threadpool import ThreadPool,makeRequests
from requests.utils import dict_from_cookiejar

from gevent import monkey;monkey.patch_all()
from three_operators.china_unicom.addtional.unicom_date import getDateSuq

from public.share_func import userAgent, basicRequest, checkParamFormat,searchPhoneInfo


class PersonUnicom(object):
    '''中国联通爬虫'''

    def __init__(self):

        self.headers = {
            'Accept': '*/*',
            'User-Agent': None,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.cookies  = dict()
        self.headers['User-Agent'] = userAgent()
    # end


    @staticmethod
    def getTimestamp(length=13):
        ''' 根据参数长度生成时间戳
        :param length: 时间戳长度
        :return: 时间戳字符串/抛出异常
        '''

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
        ''' 登录流程(函数嵌套的方式)
        :return: sysCheckLogin()
        '''

        def sysCheckLogin():
            ''' 登录检查,更新cookies
            :return: loginByJS()/dict
            '''

            url = 'http://iservice.10010.com/e3/static/check/checklogin/?_=' + self.getTimestamp()
            self.headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':None, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                self.cookies.update(dict_from_cookiejar(response.cookies))
                return loginByJS()
            else:
                return dict(result=4000, func='sysCheckLogin')
        # end

        def loginByJS():
            ''' 通过get登录,更新cookies
            :return: judgeLogin(response)/dict()
            '''

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
            params['userName'] = self.phone_info['phone']
            params['password'] = self.phone_info['password']

            url = 'https://uac.10010.com/portal/Service/MallLogin'
            self.headers['Referer'] = 'http://uac.10010.com/portal/hallLogin'
            options = {'method':'get', 'url':url, 'params':params, 'cookies':None, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                return judgeLogin(response)
            else:
                return dict(result=4000, func='loginByJS')
        # def

        def judgeLogin(response):
            ''' 对登录response进行分析
            :param response: response obj
            :return: 登录状态码dict()/raise
            '''

            try:
                code = re.search(r'resultCode:"(.*?)"', response.text).group(1)
            except (AttributeError,IndexError) as ex:
                return dict(result=4000, func='judgeLogin')
            else:
                if code == '0000':      # 登录成功
                    print 'loginSys finish'
                    self.cookies.update(dict_from_cookiejar(response.cookies))
                    return dict(result=2000, error='no error' )

                elif code == '7007':    # 密码出错
                    print 'pw error'
                    return dict(result=4401, error='pw error')

                elif code == '7999':    # 系统繁忙
                    print 'sys busy'
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
        return sysCheckLogin()
    # end


    def clawUserInfo(self):
        ''' 爬取用户信息
        :return: sysCheckLoginAgain()
        '''

        def sysCheckLoginAgain():
            ''' 检查是否登录
            :return: getHeaderView()
            '''

            url = 'http://iservice.10010.com/e3/static/check/checklogin/?_=' + self.getTimestamp()
            self.headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':self.cookies, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                return getHeaderView()
            else:
                return dict(result=4000, func='sysCheckLoginAgain')
        # def

        def getHeaderView():
            ''' 获得balance(余额)/open_date(开户时间)/cert_id(证件号)
            :return: saveUserInfos(part_info)/dict()
            '''

            url = 'http://iservice.10010.com/e3/static/query/headerView'
            self.headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'cookies':self.cookies, 'headers':self.headers}

            response = basicRequest(options)
            if response: #
                part_info = parsePartBasicInfo(response.text)
                return saveUserInfos(part_info)
            else:
                return dict(result=4000, func='getHeaderView')
        # def

        def parsePartBasicInfo(text):
            '''Get user's a part of basic info '''

            part_info = dict()
            result = json.loads(text, encoding='utf-8')

            part_info['balance'] = result['result']['account']
            part_info['open_date'] = result['userinfo']['opendate']
            part_info['cert_id'] = result['userinfo']['certnum']
            # part_info['home'] = getBelongPos()
            part_info['home'] = '深圳'    # 不要请求联通的归属地，通过百度的api传进来

            return part_info
        # def


        def saveUserInfos(part_info):
            ''' 获得用户信息
            :param part_info: dict(cert_id=XX, balance=XX, open_date=XX)
            :return:
            '''

            params = { '_':'1468549625712', 'menuid':'000100030001'}

            params['_'] = self.getTimestamp()
            url = 'http://iservice.10010.com/e3/static/query/searchPerInfo/'
            self.headers['Referer'] = 'http://iservice.10010.com/e3/query/personal_xx.html'
            options = {'method':'post', 'url':url, 'params':params, 'cookies':self.cookies, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                part_info.update(self.phone_info)
                return 2000
                # user = parseUserJson(response.text, part_info)
                # if user:
                #     inser_user = t_china_unicom_user_insert(user)
                #     return inser_user
                # else:
                #     return dict(result=5000, error='parseUserJson failed')
            else:
                return dict(result=4000, func='clawCallRecords')
        # def
        print 'start claw user info'
        return sysCheckLoginAgain()
    # end


    def clawCallInfo(self):

        def clawMonthCall(month):

            text = clawPageCall(month)
            try:
                page_json = json.loads(text, encoding='utf8')
            except (ValueError,Exception):
                return
            if 'errorMessage' in page_json.keys():  # 存在错误
                return
            else:
                text_seq.append(text)
                total_record = float(page_json['totalRecord'])
                # remain_page = int(ceil((total_record-100)/ 100))
                remain_page = int(ceil((total_record-20)/ 20))
                if remain_page > 0:
                    print '请注意,{0}月份还有{1}页'.format(month[0], remain_page)

                    coroutine_obj = list()
                    for page in range(2, 2+remain_page):
                        coroutine_obj.append(gevent.spawn(coroutineClawPageCall, month, page))
                    gevent.joinall(coroutine_obj)
                else:
                    pass
        # def

        def coroutineClawPageCall(date_tuple, page_no=1, resend = 2):  #完成单次请求[存在网络繁忙则重传]
            '''完成单次请求'''
            print '注意:协助准备处理{0}日到{1}日记录中的第{2}页'.format(date_tuple[0], date_tuple[1], page_no)

            params = { '_':'1468549625712', 'menuid':'000100030001'}
            # form = {'pageNo':'1', 'pageSize':'100', 'beginDate':'2016-07-01', 'endDate':'2016-07-18'}
            form = {'pageNo':'1', 'pageSize':'20', 'beginDate':'2016-07-01', 'endDate':'2016-07-18'}

            form['pageNo'] = page_no
            form['beginDate'] = date_tuple[0]
            form['endDate'] = date_tuple[1]
            params['_'] = self.getTimestamp()

            url = 'http://iservice.10010.com/e3/static/query/callDetail'
            self.headers['Referer'] = 'http://iservice.10010.com/e3/query/call_dan.html?menuId=000100030001'
            options = {'method':'post', 'url':url, 'form':form, 'params':params, 'cookies':self.cookies, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                try:
                    page_json = json.loads(response.text, encoding='utf8')
                except ValueError:
                    pass
                else:
                    if 'errorMessage' in page_json.keys() and  resend > 0: # 存在系统繁忙
                        try:
                            if page_json['errorMessage']['respCode'] == '4114030193':
                                return clawPageCall(date_tuple, page_no, resend-1)     # 繁忙重传
                        except KeyError:
                            pass
                    else:
                        text_seq.append(response.text)
                        print '注意:协助完成处理{0}日到{1}日记录中的第{2}页'.format(date_tuple[0], date_tuple[1], page_no)

            else:
                pass
        # def


        def clawPageCall(date_tuple, page_no=1, resend = 2):  #完成单次请求[存在网络繁忙则重传]
            '''完成单次请求'''

            params = { '_':'1468549625712', 'menuid':'000100030001'}
            # form = {'pageNo':'1', 'pageSize':'100', 'beginDate':'2016-07-01', 'endDate':'2016-07-18'}
            form = {'pageNo':'1', 'pageSize':'20', 'beginDate':'2016-07-01', 'endDate':'2016-07-18'}

            form['pageNo'] = page_no
            form['beginDate'] = date_tuple[0]
            form['endDate'] = date_tuple[1]
            params['_'] = self.getTimestamp()

            url = 'http://iservice.10010.com/e3/static/query/callDetail'
            self.headers['Referer'] = 'http://iservice.10010.com/' \
                                      'e3/query/call_dan.html?menuId=000100030001'

            options = {'method':'post', 'url':url, 'form':form,
                       'params':params, 'cookies':self.cookies, 'headers':self.headers}

            response = basicRequest(options)
            if response:
                try:
                    page_json = json.loads(response.text, encoding='utf8')
                except ValueError:
                    return False
                else:
                    if 'errorMessage' in page_json.keys() and  resend > 0: # 存在系统繁忙
                        try:
                            if page_json['errorMessage']['respCode'] == '4114030193':
                                return clawPageCall(date_tuple, page_no, resend-1)     # 繁忙重传
                        except KeyError:
                            return False
                    else:
                        return response.text
            else:
                return False
        # def



        print '测试:多线程开始爬取6个月数据'

        t_start = time.time()
        text_seq = list()
        date_seq = getDateSuq()

        pool = ThreadPool(3)
        requests = makeRequests(clawMonthCall, date_seq)
        [pool.putRequest(req) for req in requests]
        pool.wait()

        print '结束:所有的通话记录数据的总页数为：{0}'.format(len(text_seq))
        print '统计:爬取通话记录耗费{0}秒'.format(time.time() - t_start)
        for i in text_seq:
            print i
        return 2000

        # rows = parseCallJson(text_seq)
        # return t_china_unicom_call_insert(rows)
    # end




    def logoutSys(self):
        '''logout without check'''

        url = 'http://iservice.10010.com/e3/static/common/logout?_=' + self.getTimestamp()
        options = {'method':'post', 'url':url, 'cookies':None, 'headers':self.headers}

        response = basicRequest(options,resend_times=0)
        if response:
            return dict(result=2000)
        else:
            pass
    # end


    def startSpider(self, phone_num, password):

        phone_info = searchPhoneInfo(phone_num)

        if phone_info and phone_info['company'] == u'中国联通':
            self.phone_info = phone_info
            self.phone_info['password'] = password

            t_start = time.time()
            login_result = self.loginSys()
            print '时间:登录耗费{0}秒'.format(time.time() - t_start)

            if login_result['result'] == 2000:
                t_start = time.time()
                user = self.clawUserInfo()     # 爬取用户信息
                print '时间:爬取用户信息耗费{0}秒'.format(time.time() - t_start)

                call = self.clawCallInfo()     # 爬取通话记录

                if user==2000 and call == 2000:
                    return dict(result=2000)
                else:
                    print u'失败'
            else:
                return login_result
        else:
            return 'no phone info,phone number err'
    # end

# class



def chinaUnicomAPI(phone_num=None, password=None):  # API
    '''
    :param phone_num: 全为数字的字符串
    :param password: 全为数字的字符串(长度不少于6位)
    :return:
    '''

    check = checkParamFormat(phone_num, password)
    if check == True:
        demo = PersonUnicom()
        result = demo.startSpider(phone_num, password)
        return result
    else:
        return check
# end


print chinaUnicomAPI('13267175437','251314')
# print apiChinaUnicom('18617112670', '662670')
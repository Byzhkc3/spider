#coding=utf-8

import time,os
import random
import Image
import json
from requests.exceptions import *
from requests import request
from lxml import etree

from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)


def getRandIntDemo1(num):

    result = ''
    for i in range(num):
        result += str(random.randint(1, 200000))
    return result


def getTimestamp(length=13):

    if isinstance(length, int) and length >= 10:
        random_num = str(random.randint(1,10000000))
        temp = str(time.time()).split('.')
        temp = ''.join(temp)
        if len(temp) > length:
            return temp[0:length] + getRandIntDemo1(5)
        else:
            return temp + '0' * (length - len(temp)) + getRandIntDemo1(5)
    else:
        raise TypeError('the type/value of param is wrong')
# end


def getIp():
    '''构造ip'''

    a = random.randint(128, 223)
    b = random.randint(128, 223)
    c = random.randint(128, 223)
    d = random.randint(128, 223)
    return '{0}.{1}.{2}.{3}'.format(a,b,c,d)

# end getIp



def basicRequest(options, resend_times=3):

    ''' 根据参数完成request请求，成功则返回response,失败返回False
    :param options: 请求参数
    :param resend_times: 重发次数
    :return: response对象或False
    example:
    options = {
        'method':'get',
        'url':'http://www.eprc.com.hk/EprcWeb/multi/transaction/login.do',
        'form':None,
        'params':None,
        'cookies':None,
        'headers':headers,
    }
    response = basicRequest(options)
    '''

    keys = options.keys()
    options['timeout'] = options['timeout'] if 'timeout' in keys else 3
    # proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}

    try:
        response = request(
            options['method'],
            options['url'],
            timeout = options['timeout'],
            # proxies = proxies if 'proxies' not in keys else None,
            verify = options['verify'] if 'verify' in keys else False,
            data = options['form'] if 'form' in keys else None,
            params = options['params'] if 'params' in keys else None,
            cookies = options['cookies'] if 'cookies' in keys else None,
            headers = options['headers'] if 'headers' in keys else None,
            stream =  options['stream'] if  'stream' in keys else False,
        )
    except (ConnectionError,ConnectTimeout,Timeout) as time_out:
        # print options['url'],time_out
        if resend_times > 0:
            time.sleep(random.uniform(1,2))  # 中断1~2秒
            options['timeout'] += 1
            return basicRequest(options, resend_times-1)
        else:
            return False

    except ProxyError as proxy_error:
        # print proxy_error
        if resend_times > 0 :
            options['proxies'] = None
            return basicRequest(options, resend_times-1)
        else:
            return False

    except SSLError as ssl_error:
        # print ssl_error
        if resend_times > 0 :
            options['verify'] = False
            return basicRequest(options, resend_times-1)
        else:
            return False

    except Exception as ex: #注意:存在未分类异常,错误为HTTPConnectionPool(host='shixin.court.gov.cn', port=80): Read timed out.
        print '注意:存在未分类异常,错误为{0}'.format(ex)

    else:
        return response
# end


def userAgent():
    '''Generate a "user_agent" randomly and return'''

    user_agent_list = [
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.69 Safari/537.36 QQBrowser/9.1.3876.400'
    ]
    return random.choice(user_agent_list)
# end


def xpathText(resonse_text, path_dict):
    ''''Extract text by the path dictionary'''

    if isinstance(path_dict,dict):

        keys = path_dict.keys()
        result_dict = dict(zip(keys, [False]*len(keys)))
        selector = etree.HTML(resonse_text)

        for key,value in path_dict.iteritems():
            try:
                result_dict[key] = selector.xpath(value)[0].strip()
            except IndexError:
                pass
        return result_dict
    else:
        raise TypeError('Inappropriate argument type')
# end


def binaryzationImage(image):
    '''The image binarization'''

    img = Image.open(image)
    # img = img.convert('L')
    pixdata = img.load()

    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if pixdata[x, y][0] < 90:
                pixdata[x, y] = (0, 0, 0, 255)
        # for
    # for
    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if pixdata[x, y][1] < 136:
                pixdata[x, y] = (0, 0, 0, 255)
        # for
    # for
    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if pixdata[x, y][2] > 0:
                pixdata[x, y] = (255, 255, 255, 255)
        # for
    # for
    return img
# end


def saveImage(response, dire='code', name='', format='.jpg'):

    path = os.path.join(os.getcwd(), dire)
    if not os.path.exists(path):
        os.mkdir(path)

    image_path = os.path.join(path, getTimestamp() + str(name) + format)
    with open(image_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):   #chunk_size=1024
            if chunk :
                f.write(chunk)
                f.flush()

    return image_path
# end



def searchPhoneInfoBySelenium(phone_num):  # 通过百度查询手机的归属地
    '''
    :param phone_num: phone number
    :return:dict(phone=XX, province=XX, city=XX, company=XX)/raise ValueError

    example:
        >>searchPhoneInfoBySelenium('15802028888')
        {'phone':'15802028888', 'province':'广东', 'city':'广州', 'company':'中国移动'}
    '''

    import re
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException

    time_wait_usual = 2

    browser = webdriver.Chrome()
    browser.get('https://www.baidu.com')
    browser.implicitly_wait(time_wait_usual)

    browser.find_element_by_id("kw" ).send_keys(phone_num)      # 定位输入框并输入内容
    browser.find_element_by_xpath('//input[@id="su"]').click()  # 定位百度一下按钮进行查询
    browser.implicitly_wait(time_wait_usual)

    try:
        text = browser.find_element_by_xpath('//div[@class="op_mobilephone_r"]').text
        browser.close()
    except (NoSuchElementException,AttributeError):
        return dict(result=False, error='phone number is invalid')
    else:
        phone = re.search('\d.*\d', text).group()

        if phone == phone_num:
            phone_info = dict()
            record = text.split()
            phone_info['phone'] = phone
            phone_info['province'] = record[1]
            phone_info['city'] = record[2]
            phone_info['company'] = record[3]
            return dict(result=True, info=phone_info)
        else:
            raise ValueError('demoSearchPhoneHome has error')
# end


def checkParamFormat(phone_num, password):
    '''
    :param phone_num: 手机号
    :param password: 密码
    :return:
    '''
    if isinstance(phone_num,str) and isinstance(password,str):
        if len(phone_num) < 11 or len(password) < 6:
            return dict(result=1001, error="parameter's length error")
        else:
            return True
    else:
        return dict(result=1000, error="parameter's type error")
# end



def searchPhoneInfo(phone_num):
    '''
    :param phone_num: phone number
    :return:dict(phone=XX, province=XX, city=XX, company=XX)/raise ValueError

    example:
        >>searchPhoneInfo('15802028888')
        {'phone':'15802028888', 'province':'广东', 'city':'广州', 'company':'中国移动'}
    '''

    phone_status = 6855 if str(phone_num)[0] == '0' else 6004
    url = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php'
    params = {'query':phone_num, 'resource_id':phone_status}

    options = {'method':'get','url':url,'params':params}
    response = basicRequest(options)

    if response:
        try:
            item = json.loads(response.text, encoding='utf-8')['data'][0]

            return dict(
                phone = phone_num,
                province = item['prov'],
                city = item['city'],
                company = item['type'],
            )
        except (ValueError,KeyError,IndexError,Exception):
            return False

    else:
        return False
# end


def test_searchPhoneInfoBySelenium():     # 测试"searchPhoneInfoBySelenium"函数

    s1 =time.time()
    result = searchPhoneInfoBySelenium('15802028888')
    print time.time() - s1
    if result['result']:
        for k,v in result['info'].items():
            print k,v
    else:
        print result
# end


def test_searchPhoneInfo():

    start = time.time()
    result = searchPhoneInfo('13267175437')
    print 'api耗费时间为{0}秒'.format(time.time() - start )

    if result:
        for k,v in result.items():
            print k,v
    else:
        print 'api failed'

# test_searchPhoneInfo()
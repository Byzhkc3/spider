#coding=utf-8
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import DesiredCapabilities

_time_wait_usual = 10

def searchPhoneInfoBySelenium(phone_num):  # 通过百度查询手机的归属地
    '''
    :param phone_num: phone number
    :return:dict(phone=XX, province=XX, city=XX, company=XX)/raise ValueError

    example:
        >>searchPhoneInfoBySelenium('15802028888')
        {'phone':'15802028888', 'province':'广东', 'city':'广州', 'company':'中国移动'}
    '''
    capabilities = DesiredCapabilities.PHANTOMJS.copy()
    # user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) /52.0.2743.116 Safari/537.36"
    # capabilities["phantomjs.page.settings.userAgent"] = user_agent
    # capabilities["javascriptEnabled"] = False
    capabilities["phantomjs.page.settings.loadImages"] = False  # 禁止加载图片,默认加载
    # dcap["phantomjs.page.settings.resourceTimeout"] = 5000  # 超时时间，单位是 ms
    browser = webdriver.PhantomJS(desired_capabilities=capabilities)
    # browser = webdriver.PhantomJS(executable_path=r'C:\driver\phantomjs-2.1.1-windows\bin\phantomjs.exe', desired_capabilities=capabilities) # 测试win下的phantomjs驱动
    # browser = webdriver.Chrome(executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe', desired_capabilities=capabilities)    # 测试chromedriver驱动
    browser.get('https://www.baidu.com')
    browser.implicitly_wait(_time_wait_usual)
    browser.find_element_by_id("kw" ).send_keys(phone_num)      # 定位输入框并输入内容
    browser.find_element_by_xpath('//input[@id="su"]').click()  # 定位百度一下按钮进行查询
    browser.implicitly_wait(_time_wait_usual)

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


def test_searchPhoneInfoBySelenium():
# 测试"searchPhoneInfoBySelenium"函数
    print 'start now'
    s1 =time.time()
    result = searchPhoneInfoBySelenium('15802028888')
    print time.time() - s1
    if result['result']:
        for k,v in result['info'].items():
            print k,v
    else:
        print result
# end

if __name__ == '__main__':
    test_searchPhoneInfoBySelenium()
#coding=utf-8
from selenium import webdriver

#　http://www.cnblogs.com/fnng/p/3269450.html
def getCookies(cookies_seq):
    # 转换cookies
    cookie_dict = dict()
    if cookies_seq:
        for cookie in cookies_seq:
            cookie_dict[cookie['name']] = cookie['value']
    return cookie_dict


def searchPhoneInfoBySelenium(a):
    pass


def getNoteCode():

    import time
    cookies_temp = searchPhoneInfoBySelenium('15802027662')
    driver = webdriver.Chrome(r'C:\driver\chromedriver.exe')

    print '1'
    driver.get("http://www.baidu.com/")
    #向cookie的name 和value添加会话信息。
    #遍历cookies中的name 和value信息打印，当然还有上面添加的信息
    for cookie in driver.get_cookies():
        print "%s -> %s" % (cookie['name'], cookie['value'])

    print '2'
    for cookie in cookies_temp:
        driver.add_cookie(dict(name=cookie['name'], value=cookie['value']))

    for cookie in driver.get_cookies():
        print "%s -> %s" % (cookie['name'], cookie['value'])


    # 下面可以通过两种方式删除cookie
    # 删除一个特定的cookie
    # driver.delete_cookie("CookieName")
    # 删除所有cookie
    driver.delete_all_cookies()

    driver.close()


def testAgain():
    # coding=utf-8
    from selenium import webdriver
    import time

    driver = webdriver.Chrome(r'C:\driver\chromedriver.exe')

    driver.get("http://www.baidu.com/")

    # 向cookie的name 和value添加会话信息。
    driver.add_cookie({'name': 'key-aaaaaaa', 'value': 'value-bbbb'})

    # 遍历cookies中的name 和value信息打印，当然还有上面添加的信息
    for cookie in driver.get_cookies():
        print "%s -> %s" % (cookie['name'], cookie['value'])

    # 下面可以通过两种方式删除cookie
    # 删除一个特定的cookie
    driver.delete_cookie("CookieName")
    # 删除所有cookie
    driver.delete_all_cookies()

    driver.close()


def test_selenium_cookies():
    pa

if __name__ == '__main__':
    # print searchPhoneInfoBySelenium('15802027662')
    # testAgain()
    getNoteCode()
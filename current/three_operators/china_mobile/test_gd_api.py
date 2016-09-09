#coding=utf-8

'''
测试广东中国移动API
'''

import time
from gd_china_mobile import apiGDChinaMobile

demo = apiGDChinaMobile('15802027662','20168888')

if demo['result'] == 200:   #密码发送成功

    time.sleep(3)
    login_code = raw_input('请输入登录密码:')

    result = apiGDChinaMobile('15802027662','20168888',login_code)
    if result['result'] == 2000:    # 流程成功
        print 'ok'
    else:
        print result['error']

else:
    print demo

#coding=utf-8
import time
from person_unicom import apiChinaUnicom

phone_num = '13267175437'
password = '251314' # raw_input('Please input your password:')

s1 =  time.time()
record  = apiChinaUnicom(phone_num=phone_num, password=password)
print time.time()-s1
code = record['result']

if  code == 2000:
    print '流程成功'
elif code == 1000 or code == 1001:    #参数类型错误
    print '参数类型错误'

elif code == 4400 :  # 用户名或者密码错误
    print  '账号错误'
elif code == 4401 :
    print  '密码错误'

elif code == 4404:
    print '手机号无效'

else:
    try:
        print record['error']
    except KeyError:
        print record['func']








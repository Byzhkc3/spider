#coding=utf-8
from necessary.phone_attr import getAttributes
# 运营商入口


# 接口文档
def searchOperatorInfo(phone=None):
    phone = '13267175437'
    attr = getAttributes(phone)
    if attr:
        if attr['company'] == 1: # 联通
            print '调用中国联通接口'
        elif attr['company'] == 2: # 移动
            print '调用中国移动接口'
        elif attr['company'] == 3: # 电信
            print '调用中国电信接口'
        else:
            print '不在处理范围内'

if __name__ == '__main__':
    searchOperatorInfo()


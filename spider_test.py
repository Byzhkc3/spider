#coding=utf-8
import time
from spider import getAttributes
from spider import chinaUnicomAPI
from spider import phonebookSpiderAPI
from spider import shixinSearchAPI, zhixingSearchAPI

def countTime(t_begin):
    pass


# 测试-查询手机属性
def searchPhoneInfo_Test():
    import time
    start = time.time()
    result = getAttributes('15802027662')
    print 'api耗费时间为{0}秒'.format(time.time() - start )
    if result:
        for k,v in result.items():
            print k,v
    else:
        print 'api failed'
# end


# 测试-联通接口
def chinaUnicomAPI_Test():
    t_begin = time.time()
    attr = getAttributes('13267175437')
    if attr['code'] == 2000:
        phone_attr = attr['data']
        phone_attr['password'] = 'moyihua251314'
        result = chinaUnicomAPI(phone_attr)
        for item in result.items():
            print item
    else:
        print '无法查询号码的归属信息,bye!'
    print u'整个流程耗费用时:{0}'.format(time.time()-t_begin)
# end


# 测试-失信被执行人
def shixinSearchAPI_Test():
    t_begin = time.time()
    print time.ctime() + ':\t' + 'Test start, running'
    card_num = '72217220X'
    name = '遵义侨丰房地产开发有限责任公司'
    # card_num = ''
    # name = u'毛泽东'
    results = shixinSearchAPI(name, card_num)
    print time.ctime() + ':\t' + 'Test over, cost: {0} seconds\n\n'.format(time.time()-t_begin)
    print results
# end


# 测试-被执行人接口
def zhixingSearchAPI_Test():
    t_begin = time.time()
    print time.ctime() + ':\t' + 'Test start'
    card_num = '77535404-X'
    name = '漳州伟翔精密机械有限公司'
    # card_num = ''
    # name = '何计通'
    results = zhixingSearchAPI(name, card_num)
    print time.ctime() + ':\t' + 'Test over, cost: {0} seconds\n'.format(time.time()-t_begin)
    print results
# end


# 测试-政府联络方式
def phonebookSpiderAPI_Test():
    phonebookSpiderAPI()
# end


if __name__ == '__main__':
    searchPhoneInfo_Test()
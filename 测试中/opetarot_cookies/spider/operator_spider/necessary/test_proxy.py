#coding=utf-8
import json
import gevent
import time
from gevent._semaphore import Timeout
import requests
from requests.exceptions import ProxyError, SSLError
from spider.public import basicRequest,returnResult
from gevent import monkey; monkey.patch_all()


_all_record = list()


class Proxy(object):
    proxies_seq = [
        {'http': 'http://hanyun32_756:hanyun32_756@45.34.68.251:8080',
         'https': 'http://hanyun32_756:hanyun32_756@45.34.68.251:8080'},

        {'http': 'http://hanyun32_882:hanyun32_882@45.34.68.252:8080',
         'https': 'http://hanyun32_882:hanyun32_882@45.34.68.252:8080'},

        {'http': 'http://hanyun32_978:hanyun32_978@45.34.68.253:8080',
         'https': 'http://hanyun32_978:hanyun32_978@45.34.68.253:8080'},

        {'http': 'http://hanyun33_110:hanyun33_110@45.34.68.254:8080',
         'https': 'http://hanyun33_110:hanyun33_110@45.34.68.254:8080'},

        {'http': 'http://hanyun33_416:hanyun33_416@23.228.213.130:8080',
         'https': 'http://hanyun33_416:hanyun33_416@23.228.213.130:8080'},

        {'http': 'http://hanyun34_26:hanyun34_26@23.228.213.131:8080',
         'https': 'http://hanyun34_26:hanyun34_26@23.228.213.131:8080'},
        ]
# class

_company_convert = {
    u'中国联通': 1,
    u'中国移动': 2,
    u'中国电信': 3
}

def getPhoneAttr(proxies=None):
    """ 调用百度api获得手机的归属地
    :param phone_num: 手机号
    :return:统一接口返回
    example:
        >>searchPhoneInfo('15802028888')
        正常返回key data对应的元素例子
        {'phone':'13267175437', 'province':'广东', 'city':'深圳', 'company':1}
        company值:中国联通1; 中国移动2; 中国电信3, 其他4
    """
    phone_num = 15802027662
    phone_status = 6855 if str(phone_num)[0] == '0' else 6004
    url = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php'
    params = {'query':phone_num, 'resource_id': phone_status}
    options = {'method': 'get', 'url': url, 'params': params, 'proxies': proxies}

    response = basicRequest(options)
    if response:
        try:
            company_type = 4
            item = json.loads(response.text)['data'][0]
            if item['type'] in _company_convert.keys():
                company_type =  _company_convert[item['type']]
            data = {
                'phone': phone_num,
                'province': item['prov'],
                'city': item['city'],
                'company': company_type
            }
            item = returnResult(code=2000, data=data, desc=u'查询成功')
            _all_record.append(item)
        except (KeyError, IndexError):
            return returnResult(code=4500, data={})
        except (ValueError, Exception):
            return returnResult(code=4100, data={})
    else:
        return returnResult(code=4000, data={})
# end

def getPhoneAttr_Test():
    for proxies in Proxy.proxies_seq:
        objs = list()
        for i in range(500):
            objs.append(gevent.spawn(getPhoneAttr, proxies))
        gevent.joinall(objs)
# end

if __name__ == '__main__':
    # print getPhoneAttr()
    getPhoneAttr_Test()
    print len(_all_record)

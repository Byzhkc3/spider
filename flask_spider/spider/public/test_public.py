import time
from share_func import Request

Request.proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}
options = {'method':'get', 'url': 'https://www.baidu.com/'}
response = Request.basic(options)
print response.text
time.sleep(10)

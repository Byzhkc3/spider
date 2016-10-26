import time
from share_func import Request


def getText():
    options = {'method':'get', 'url': 'https://www.baidu.com/'}
    response = Request.basic(options)
    return response.text
# end

def testAPI(proxies = {'http':'http://127.0.0.1:8888','https':'http://127.0.0.1:8888'}):
    Request.proxies = proxies
    text = getText()
    print text
    time.sleep(10)
# end

if __name__ == '__main__':
    testAPI()
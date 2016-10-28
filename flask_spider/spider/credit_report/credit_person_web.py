#coding=utf-8
import os,random
from io import BytesIO
from PIL import Image
from lxml import etree
from pytesseract import image_to_string
from requests.utils import dict_from_cookiejar
from spider.public import returnResult
from spider.public import userAgent, basicRequest, xpathText


class CreditReport(object):
    """简版征信报告"""
    def __init__(self, name, password, auth_code):
        """
        :param name: 用户名
        :param password: 登陆密码
        :param auth_code: 身份验证码
        """
        self.headers = {
            'Referer': None,
            'Accept-Language': 'zh-CN',
            'Connection': 'keep-alive',
            'Host': 'ipcrs.pbccrc.org.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
            'User-Agent': userAgent()
        }
        self.threshold = 10
        self.cookies  = None
        self.host = 'https://ipcrs.pbccrc.org.cn'
        self.section = dict(user_name=name, password=password, id_code=auth_code)
    # end

    def visitSys(self):
        '''Visit the home page'''
        url = 'https://ipcrs.pbccrc.org.cn/'
        options = {'method':'get', 'url':url, 'form':None,
                   'params':None, 'cookies':None, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            self.cookies = dict_from_cookiejar(response.cookies)
            return self.visitLoginpage()
        else:
            return dict(result=4000, error='visitSys funciton')
    # end


    def visitLoginpage(self):
        '''Visit the login page'''
        url = 'https://ipcrs.pbccrc.org.cn/login.do?method=initLogin'
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/index1.do'
        options = {'method':'get', 'url':url, 'form':None, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            path_dict = dict(date = '//input[@name="date"]/@value',
                             code_url = '//img[@id="imgrc"]/@src',
                             token = '//input[@name="org.apache.struts.taglib.html.TOKEN"]/@value')

            result = xpathText(response.text, path_dict)
            if result['date'] and result['code_url'] and result['token']:
                code = self.getCode(self.host+result['code_url'])
                form_item = dict(token=result['token'], date=result['date'], code=code)
                return self.loginSys(form_item)
            else:
                return dict(result=4100, error='xpath not found')
        else:
            return dict(result=4000, error='visitLoginpage function')
    # end

    @staticmethod
    def recogImage(content):
        """ 识别只有数字的简单验证码
        :param content: response.content
        :return: 识别结果/False """
        file = BytesIO(content)
        img = Image.open(file)
        img = (img.convert('L')).resize((200,65))
        result = image_to_string(img).strip()
        print result
        result = result if result.isalnum() else False
        img.close()
        file.close()
        return result
    # end

    def getCode(self, url, save_path='./code'):
        '''Download code image and then invoke the recogImage function '''
        options = {'method':'get', 'url':url, 'form':None, 'stream':True,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            return self.recogImage(response.content)
        else:
            return dict(result=4000, error='getNoteCode function')
    # end


    def updateCode(self, save_path='./code'):
        '''Verify fail and download new picture'''
        url = 'https://ipcrs.pbccrc.org.cn/imgrc.do?a=' + str(random.randint(1467967606991,1767967607647))
        options = {'method':'get', 'url':url, 'form':None, 'stream':True,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            return self.recogImage(response.content)
        else:
            return dict(result=4000, error='updateCode function')
    # end

    def loginSys(self, form_item):
        '''Login the system'''
        form = {
            'org.apache.struts.taglib.html.TOKEN':'1ec8589094a44e23e603c901536bbc59',
            'method':'login',
            'date':'1467878083784',
            'loginname':'luocx1988',
            'password':'pbocmm2670',
            '_@IMGRC@_':'gr3qga'
        }
        form['date'] = form_item['date']
        form['_@IMGRC@_'] = form_item['code']
        form['password'] = self.section['password']
        form['loginname'] = self.section['user_name']
        form['org.apache.struts.taglib.html.TOKEN'] = form_item['token']

        url = 'https://ipcrs.pbccrc.org.cn/login.do'
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/page/login/loginreg.jsp'
        options = {'method':'post', 'url':url, 'form':form, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            error = self.loginError(response.text)
            if error['error'] == None:
                return self.welcomePage()
            elif error['error'] == 'code': # code error
                if self.threshold > 0:
                    self.threshold -= 1
                    form_item['code'] = self.updateCode()
                    return self.loginSys(form_item)
                else:
                    return dict(result=4200, error='image recognition failed')
            elif error['error'] == 'user_name': # use_name or pw error
                return dict(result=4600, error='user_name or pw error')
        else:
            return dict(result=4000, error='loginByJS function')
    # end


    def loginError(self, text):
        '''Verify error of verification code/user_name/password'''
        selector = etree.HTML(text)
        error = selector.xpath('//div[@class="erro_div3"]')
        if len(error) == 1: # exist error
            if error[0].xpath('//span[@id="_@MSG@_"]/text()'): # code error
                return dict(error='code')
            elif error[0].xpath('//span[@id="_error_field_"]/text()'): # name or pw error
                return dict(error='user_name')
        else:   # no error
            return dict(error=None)
    # end


    def welcomePage(self):
        '''Visit the welcome page afer login sucessfully'''
        url = 'https://ipcrs.pbccrc.org.cn/welcome.do'
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/login.do'
        options = {'method':'get', 'url':url, 'form':None, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            return self.inputIdCode()
        else:
            return dict(result=4000, error='welcomePage function')
    # end


    def inputIdCode(self):
        '''Give the id_code to Sys'''
        form = {
            'method':'checkTradeCode',
            'code':'e5pkaa',
            'reportformat':'21'
        }
        form['code'] = self.section['id_code']
        url = 'https://ipcrs.pbccrc.org.cn/reportAction.do'
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/reportAction.do?method=queryReport'
        options = {'method':'post', 'url':url, 'form':form, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            if (response.text).strip() == str(0):
                return self.acquireReport()
            else:
                return dict(result=4444, error='auth_code error')
        else:
            return dict(result=4000, error='inputIdCode function')
    # end


    def acquireReport(self):
        '''Claw person credit information'''
        form = {
            'tradeCode':'e5pkaa',
            'reportformat':'21'
        }
        form['tradeCode'] = self.section['id_code']
        url = 'https://ipcrs.pbccrc.org.cn/simpleReport.do?method=viewReport'
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/reportAction.do?method=queryReport'
        options = {'method':'post', 'url':url, 'form':form, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            file_name = self.section['user_name'] + '.html'
            if self.saveHtml(response.text, file_name) == True:
                return dict(result=2000, file_name=file_name)
            else:
                raise ValueError(u'保存错误')
            # report_result = clawCreditReport(etree.HTML(response.text))
            # print report_result
        else:
            return dict(result=4000, error='acquireReport function')
    # end

    def saveHtml(self,text, file_name):
        """ 保存图片
        :param response: request返回对象
        :param img_dire:  当前目录下的文件夹
        :param img_name:  图片文件名
        :param img_type: 图片格式
        :return: 图片的绝对路径 """
        # win_dire = r'D:\github\moyh_work\flask_spider\templates'  # windows下测试使用的保存目录
        win_dire = r'/home/moyh/flask_spider/templates'  # ubuntu 下测试使用的保存目录
        if not os.path.exists(win_dire):
            os.mkdir(win_dire)
        file_name = os.path.join(win_dire, file_name)
        with open(file_name, 'w') as f:
            f.write(text)
        return True
    # end

    def logoutSys(self):
        '''Logout the system'''
        form = {'method':'loginOut'}
        url = 'https://ipcrs.pbccrc.org.cn/login.do?' + str(random.random())
        self.headers['Referer'] = 'https://ipcrs.pbccrc.org.cn/top2.do'
        options = {'method':'post', 'url':url, 'form':form, 'params':None,
                   'cookies':self.cookies, 'headers':self.headers}

        response = basicRequest(options)
        if response:
            return dict(result=2000)
        else:
            return dict(result=4000, error='logoutSys')
    # end

# class

def creditPersonAPI(name, password, auth_code):
    """
    :param name: 用户名
    :param password: 登录密码
    :param auth_code: 身份验证码
    :return:
    """
    person = CreditReport(name, password, auth_code)
    result = person.visitSys()
    if result['result'] == 2000:
        data = dict(file_name = result['file_name'])
        return returnResult(code=2000, data=data)
    else:
        return returnResult(code=result['result'], data={})
# end

if __name__ == '__main__':
    print u'授权查询，请谨慎测试'
    print u'如要测试，请取消注释'
    # name = 'zhouhuatang110'
    # password = 'ling920716'
    # auth_code = 'fckcag'
    # result = creditPersonAPI(name, password, auth_code)
    # for k,v in result.items():
    #     print k, '=====>', v

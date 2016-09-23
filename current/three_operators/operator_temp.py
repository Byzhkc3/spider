#coding=utf-8
import re


def judgeByMatch(pattern, string):
    # 通过match内容来判断相关类型
    try:
        re.match(pattern, string).group(1)
    except (IndexError, AttributeError):
        return False
    else:
        return True

tips= [u'\u52a8\u6001\u5bc6\u7801\u5df2\u53d1\u9001\uff0c10\u5206\u949f\u5185\u6709\u6548\u3002']
print tips[0]
print judgeByMatch('(动态密码已发送)', tips[0].encode('utf-8'))
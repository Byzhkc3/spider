from flask import Flask, render_template, session
from spider import getNoteCode
app = Flask(__name__)
app.secret_key = "test"
import pickle

_a = 1222
_phone_attr = dict(phone=1, b=2)

class Test(object):
    def __init__(self,a):
        self.__a = a

    def getNum(self):
        return self.__a + _a
# end


@app.route('/')
def example():
    result = getNoteCode(_phone_attr)
    if result['code'] == 2000:
        print 2000
        session['t'] = 1222
        return render_template("example.html")
    else:
        print 'hello,123'



if __name__ == "__main__":
    # app.run(host='127.0.0.1', port=8080)
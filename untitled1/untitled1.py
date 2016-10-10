from flask import Flask, render_template, session

app = Flask(__name__)
app.secret_key = "test"


_a = 1222
class Test():

    # def __init__(self):
    #     super(int,self).__init__()
    def __init__(self,a):
        # super(int,self).__init__()
        self.__a = a


    def getNum(self):
        return self.__a + _a




@app.route('/')
def example():
    t = Test(1)
    session['t'] = t
    return render_template("example.html")

if __name__ == "__main__":
    app.run(port=8080)
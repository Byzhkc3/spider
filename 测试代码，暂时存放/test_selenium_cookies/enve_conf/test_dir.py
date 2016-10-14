import os
print 1,str(__file__)
print 2,type(os.path.dirname(__file__))
basedir = os.path.abspath(__file__)
print 3,basedir

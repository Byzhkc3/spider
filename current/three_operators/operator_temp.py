__author__ = 'moyh'

a = dict(a=11, b=22)
key = ('a', 'b', 'c', 'd')
[a.setdefault(i,'') for i in key]
print a
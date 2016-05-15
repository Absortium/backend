__author__ = 'andrew.shvv@gmail.com'

d = {
    "a": 0
}


def s(d):
    d['a'] += 1


s(d)
print(d['a'])

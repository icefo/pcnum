__author__ = 'adrien'
import re
a = "Peuple Accuse O'hara (le)"
# http://stackoverflow.com/questions/17779744/regular-expression-to-get-a-string-between-parentheses-in-javascript
regex = re.compile(" \(([^)]+)\)$")
truc = re.search(regex, a)

if truc is not None:
    # print(len(a))
    # print(truc.group(1))
    # print(truc.start())
    # print(truc.end())
    a = a[:truc.start()]
    a = truc.group(1) + " " + a
    # return a
    print(a)
else:
    # return a
    print(a)




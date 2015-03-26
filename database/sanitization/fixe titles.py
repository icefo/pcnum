__author__ = 'adrien'
import re
value = "Peuple Accuse O'hara (le)"
# http://stackoverflow.com/questions/17779744/regular-expression-to-get-value-string-between-parentheses-in-javascript
regex = re.compile(" \(([^)]+)\)$")
truc = re.search(regex, value)

if truc is not None:
    # print(len(value))
    # print(truc.group(1))
    # print(truc.start())
    # print(truc.end())
    value = value[:truc.start()]
    value = truc.group(1) + " " + value
    # return value
    print(value)
else:
    # return value
    print(value)




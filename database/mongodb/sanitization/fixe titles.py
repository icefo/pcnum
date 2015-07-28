import re
value = "Peuple Accuse O'hara (le)"
# http://stackoverflow.com/questions/17779744/regular-expression-to-get-a-string-between-parentheses-in-javascript
regex = re.compile(" \(([^)]+)\)$")
truc = re.search(regex, value)

if truc is not None:
    # print(len(a))
    # print(truc.group(1))
    # print(truc.start())
    # print(truc.end())
    value = value[:truc.start()]
    value = truc.group(1) + " " + value
    # return a
    print(value)
else:
    # return a
    print(value)




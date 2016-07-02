from collections import OrderedDict
from backend.shared import TimedKeyDeleteDict
from uuid import uuid4
from sortedcontainers.sorteddict import SortedDict

la = ["title", "year", "dc:identifier", "start_date", "source", "action", "progress"]
l = ['75293c71-cbc4-4ab0-9038-eaa51522912f', '24ec269c-3e9d-4569-9590-0871116a7a54', '9aa268a2-179b-4042-b05d-055b3ae20a3e', '36deb919-330b-424a-8b8e-3586850891b5', '94996314-b5ff-4930-8c04-cea1d255c1c1', '62d6ad1c-0deb-4db5-a4c3-01eed4f7ccaa', '444d6a65-c873-4a06-9f67-b69e20bec1cc']

dico = SortedDict()
c = 0
for x in la:
    dico[l[c]] = {x: x + " 2" for x in la}
    c += 1

print(dico)

print(dico.index("36deb919-330b-424a-8b8e-3586850891b5"))
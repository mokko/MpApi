import sys
sys.path.append ("../src")
from MpApi import MpApi
from Search import Search

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_search():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)

    s = Search(module="Object")
    s.addCriterion(
        field="ObjRegistrarRef.RegExhibitionRef.__id",
        operator="equalsField",
        value="20222")
    s.validate(mode="search")
    api.search(xml=s.toString())
    
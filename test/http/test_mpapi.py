# -*- coding: UTF-8
# content of test_sample.py
# import chardet

from mpapi.client import MpApi
from mpapi.search import Search
from mpapi.constants import get_credentials

user, pw, baseURL = get_credentials()


def test_init():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert api


def test_getItem():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", id="993084")  # 2609893 doesnt exist in productive
    assert r.status_code == 200
    # print(r.text)  # use pytest -s to see STDOUT when it occurs
    api.toFile(xml=r.text, path="getItem.xml")
    # assert "äöü" in r.text
    # assert r.status_code == 222


def test_getSession():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    key = api.getSessionKey()
    assert key
    print(f"{key=}")


def test_getDefinition():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getDefinition()
    assert r.status_code == 200
    r = api.toFile(xml=r.text, path="getDefinitionAll.xml")


def test_getDefinition2():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    m = api.getDefinition2()
    assert m
    m.toFile(path="getDefinitionAll2.xml")


def test_search():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)

    s = Search(module="Object")
    s.addCriterion(
        field="ObjRegistrarRef.RegExhibitionRef.__id",
        operator="equalsField",
        value="20222",
    )
    s.validate(mode="search")
    api.search(xml=s.toString())

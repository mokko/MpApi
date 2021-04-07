# -*- coding: UTF-8
# content of test_sample.py
import sys
from pathlib import Path
sys.path.append ("../src")
from MpApi import MpApi

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_prep():
    assert user == "EM_BG"
    
def test_init():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert api

def test_getItem():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", id="2609893")
    assert r.status_code == 200
    #print(r.text) # use pytest -s to see STDOUT when it occurs
    api.toFile(xml=r.text, path="getItem.xml")
    assert "äöü" in r.text
    #assert r.status_code == 222

def test_getSession():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    key = api.getSessionKey()
    assert key
    print (key)
    
def test_getDefinition():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getDefinition()
    assert r.status_code == 200
    r = api.toFile(xml=r.text, path="getDefinitionAll.xml")

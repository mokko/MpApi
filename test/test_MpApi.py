# -*- coding: UTF-8
# content of test_sample.py
import chardet
import sys
import requests
from lxml import etree
from pathlib import Path
sys.path.append ("../src")
from MpApi import MpApi

with open("../sdata/credentials.py") as f:
    exec(f.read())

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

def test_different_way():
    parser = etree.XMLParser(resolve_entities=True, remove_blank_text=True) #why is the default encoding=None
    E = etree.fromstring(bytes("<?xml version=\"1.0\" encoding=\"utf-8\"?><root>äöü</root>", encoding="UTF-8"), parser)
    tree = etree.ElementTree(E)
    tree.write("writtenWithL2.xml", pretty_print=True, encoding="UTF-8") # appears to write Element
    assert type(E)
    print (type(E))
    
def test_encodings():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", id="2609893")
    encoding = chardet.detect(r.content)['encoding']
    print('GH' +encoding)
    assert r.encoding == "UTF-8"
    with open("writtenWithOpenB.xml", "wb") as f:
        f.write(bytes(r.text, encoding='utf-8')) # encodings ok.

    E = etree.XML(r.content) #parser not used
    tree = etree.ElementTree(E)
    tree.write("writtenWithL.xml", pretty_print=True, encoding="UTF-8") # appears to write Element
    #E = etree.parse(xml, parser) # returns complete doc

    #assert "äöü" in r.text
    #self.etree = etree.parse(str(path))
# -*- coding: UTF-8
import sys
sys.path.append ("../src")
from Search import Search
from Sar import Sar

with open("../sdata/credentials.py") as f:
    exec(f.read())

def test_init():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    assert sr
    
def test_getItem():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    r = sr.getItem(module="Object", id="2609893")
    assert r.status_code == 200
    assert "ä" in r.text
  
def test_getObjectSet():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    r = sr.getObjectSet(type="exhibitId", id="20222")
    assert r.status_code == 200
    
    r = sr.getObjectSet(type="groupId", id="29002")
    assert r.status_code == 200

def test_getMediaSet():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    r = sr.getMediaSet(type="exhibitId", id="20222")
    sr.toFile(xml=r.text, path="sdata/exhibit20222.xml")
    assert r.status_code == 200
    r = sr.getObjectSet(type="groupId", id="29002")
    assert r.status_code == 200
    sr.toFile(xml=r.text, path="sdata/group29002.xml")

def test_search():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)

    s = Search(module="Object")
    s.addCriterion(
        field="ObjRegistrarRef.RegExhibitionRef.__id",
        operator="equalsField",
        value="20222")
    s.validate(mode="search")
    r = sr.search(xml=s.toString())
    
def test_saveAttachments():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    xml = sr.xmlFromFile(path="sdata/exhibit20222.xml")
    sr.saveAttachments(xml=xml, dir="sdata")
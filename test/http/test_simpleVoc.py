# -*- coding: UTF-8
# content of test_sample.py
import chardet
import requests
from pathlib import Path
from lxml import etree
from pathlib import Path

from mpapi.client import MpApi
from mpapi.search import Search
from mpapi.module import Module

with open("../sdata/credentials.py") as f:
    exec(f.read())


voc = "GenLocationVgr"  # ObjIconographyKeywordProjectVgr"
voc = "ObjIconographyKeywordProjectVgr"  #


def test_init():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert api


def test_vInfo():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vInfo(instanceName=voc)
    assert r.status_code == 200
    # print(r.text) # use pytest -s to see STDOUT when it occurs
    write_file(path="../sdata/vInfo.xml", xml=r.text)


def test_vGetNodes():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetNodes(instanceName=voc)
    write_file(path="../sdata/vGetNodes.xml", xml=r.text)


def test_vGetLabels():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetLabels(instanceName=voc)
    assert r.status_code == 200
    write_file(path="../sdata/vGetLabels.xml", xml=r.text)


def test_vGetNodeClasses():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetNodeClasses(instanceName=voc)
    assert r.status_code == 200
    write_file(path="../sdata/vGetNodeClasses.xml", xml=r.text)


def test_vNodeByIdentifier():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vNodeByIdentifier(instanceName=voc, id="4254998")
    assert r.status_code == 200
    write_file(path="../sdata/vGetNodeId4254998.xml", xml=r.text)


#
# helper
#
def write_file(*, path, xml):
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    # can't pretty print xml right now b/c of encoding declaration
    # if not Path(path).exists():
    # ET = etree.fromstring(xml)
    # xml_pp = etree.tostring(xml, pretty_print=True, encoding="unicode")
    api.toFile(xml=xml, path=path)

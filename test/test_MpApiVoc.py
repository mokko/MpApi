# -*- coding: UTF-8
# content of test_sample.py
import chardet
import sys
import requests
from pathlib import Path
from lxml import etree
from pathlib import Path

sys.path.append("../src")
from MpApi import MpApi
from Search import Search

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_init():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert api


def test_vInfo():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vInfo(instanceName="GenLocationVgr")
    assert r.status_code == 200
    # print(r.text) # use pytest -s to see STDOUT when it occurs
    write_file("vInfo.xml", api, r)


def test_vGetNodes():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetNodes(instanceName="GenLocationVgr")
    write_file("vGetNodes.xml", api, r)


def test_vGetLabels():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetLabels(instanceName="GenLocationVgr")
    assert r.status_code == 200
    write_file("vGetLabels.xml", api, r)


def test_vGetNodeClasses():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vGetNodeClasses(instanceName="GenLocationVgr")
    assert r.status_code == 200
    write_file("vGetNodeClasses.xml", api, r)


def test_vNodeByIdentifier():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.vNodeByIdentifier(instanceName="GenLocationVgr", id="4220572")
    assert r.status_code == 200
    write_file("vGetNodeId4220572.xml", api, r)


#
# helper
#
def write_file(path, api, r):
    if not Path(path).exists():
        api.toFile(xml=r.text, path=path)

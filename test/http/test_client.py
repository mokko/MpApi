# -*- coding: UTF-8
# content of test_sample.py

from mpapi.client import MpApi
from mpapi.search import Search
from mpapi.module import Module
from mpapi.constants import get_credentials

user, pw, baseURL = get_credentials()

"""
    I want to test a search which shows only records changed after a certain
    since-date.
    In I do
       "Letzte Änderung" "Größer Als" "23.12.2021 12:00"
  
    In zml:
    <systemField dataType="Timestamp" name="__lastModified">
        <value>2021-11-03 09:50:39.74</value>
        <formattedValue language="en">03/11/2021 09:50</formattedValue>
    </systemField>
   
"""


def test_init():
    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert client


def tast_since():
    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    s = Search(module="Object")
    s.addCriterion(
        operator="greater",  # greater
        field="__lastModified",
        value="2021-12-23T12:00:00.0",  # date is possible 2021-12-23 dateTime Format? 2021-12-23T12:00:00.0
    )
    assert s.validate(mode="search")
    xml = s.toString()
    client.toFile(path="../sdata/searchSince.xml", xml=xml)

    r = client.search(xml=s.toString())
    assert r.status_code == 200
    print(r.text)  # use pytest -s to see STDOUT when it occurs
    client.toFile(path="../sdata/sinceTest.xml", xml=r.text)


def test_create_item():
    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    m = Module()
    objModule = m.module(name="Multimedia")
    item = m.moduleItem(parent=objModule, hasAttachments="false")
    m.toFile("debug.multmedia.xml")
    print(item)
    client.create_item3(data=m)

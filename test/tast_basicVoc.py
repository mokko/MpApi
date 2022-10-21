# from MpApi.Search import Search
from mpapi.module import Module
from mpapi.client import MpApi

with open("sdata/credentials.py") as f:
    exec(f.read())


def test_init():
    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert client

    r = client.vInfo(instanceName="ObjIconographyKeywordProjectVgr")
    print(r.text)

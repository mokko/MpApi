import sys

sys.path.append("../src")

# from MpApi.Search import Search
# from MpApi.Module import Module
from MpApi.Client import MpApi

with open("sdata/credentials.py") as f:
    exec(f.read())


def test_init():
    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert client

    r = client.vInfo(instanceName="ObjIconographyKeywordProjectVgr")
    print(r.text)
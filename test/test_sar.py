from mpapi.search import Search
from mpapi.module import Module
from mpapi.sar import Sar

with open("sdata/credentials.py") as f:
    exec(f.read())

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

"""
    Tests of SAR that dont rely on http requests
"""


def test_init():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    assert sr

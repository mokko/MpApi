from mpapi.search import Search
from mpapi.module import Module
from mpapi.sar import Sar
from mpapi.constants import get_credentials

user, pw, baseURL = get_credentials()

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

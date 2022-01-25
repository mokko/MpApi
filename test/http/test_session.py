import requests
from requests.structures import CaseInsensitiveDict
from requests.auth import HTTPBasicAuth
from mpapi.module import Module

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_nosession():
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/xml"
    headers["Accept"] = "application/xml;charset=UTF-8"
    appURL = baseURL + "/ria-ws/application"
    auth = HTTPBasicAuth(user, pw)

    url = appURL + "/module/definition"
    """ 
    We need three variables
    * URL
    * headers
    * auth (user,pw)
    """
    r = requests.get(url, headers=headers, auth=auth)
    m = Module(xml=r.text)
    m.toFile(path="definition.xml")


def test_session():
    pass

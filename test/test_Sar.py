import sys
sys.path.append("../src")

from Search import Search
from Module import Module
from Sar import Sar

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

def test_double_join():
    """
    What happens when we join two times the same record? Up to now we seem to 
    get double records, but in the future we want to get one distinct 
    moduleItems.
    """
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    path="sdata/739673.xml"
    inL = list()
    xml = sr.xmlFromFile(path=path)
    inL.append(xml)

    xml = sr.xmlFromFile(path=path)
    inL.append(xml)
    xml_new = sr.join(inL=inL)
    m = Module(xml=xml_new)
    m._dropUUID()
    m.toFile(path="sdata/debug.xml")
    #print (xml_new)
    assert m.validate()
    assert m.totalSize(module="Object") == 1
    #xml_new.xpath("count('application/modules/module[@name = 'Object'])", namespaces=NSMAP)
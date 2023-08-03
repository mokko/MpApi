# from MpApi.Search import Search
from mpapi.module import Module
from mpapi.client import MpApi
from mpapi.constants import get_credentials
from pathlib import Path
from lxml import etree
from requests.exceptions import HTTPError

user, pw, baseURL = get_credentials()
client = MpApi(baseURL=baseURL, user=user, pw=pw)
vocs = ["GenLocationVgr", "ObjIconographyKeywordProjectVgr", "AccDenominationVgr"]
IDs = {
    "AccDenominationVgr": 30109,
    "GenLocationVgr": 4208822,
    "ObjIconographyKeywordProjectVgr": 61671,
}

#
# these are not proper tests, rather these are explorations of the API
#


def write_to_file(txt, fn):
    if len(txt) == 0:
        print(f"WARNING: {fn} empty, not creating file")
        return
    else:
        print(f"{len(txt)} length")
    print(f"writing to file {fn}")
    txt = txt.encode()
    ET = etree.XML(txt)
    doc = etree.ElementTree(ET)
    doc.write(str(fn), pretty_print=True, encoding="UTF-8")  # method="c14n2"
    # with open(fn, "w") as file:
    #    file.write(txt)


#
#
#


def test_vInfo():
    for voc in vocs:
        fn = Path(f"sdata/voc/vInfo-{voc}.xml")
        # if not fn.exists():
        r = client.vGetInfo(instanceName=voc)
        write_to_file(r.text, fn)
        assert r


def test_vNodes():
    for voc in vocs:
        fn = Path(f"sdata/voc/nodes-{voc}.xml")
        # if not fn.exists():
        r = client.vGetNodes(instanceName=voc)
        write_to_file(r.text, fn)


def test_vLabels():
    for voc in vocs:
        fn = Path(f"sdata/voc/label-{voc}.xml")
        # if not fn.exists():
        r = client.vGetLabels(instanceName=voc)
        write_to_file(r.text, fn)


def test_vNodeClasses():
    for voc in vocs:
        fn = Path(f"sdata/voc/nodeClasses-{voc}.xml")
        # if not fn.exists():
        r = client.vGetNodeClasses(instanceName=voc)
        write_to_file(r.text, fn)


def test_vNodeByIdentifier():
    """This is just a lookup. Can't get it to work!"""

    for voc in vocs:
        fn = Path(f"sdata/voc/nodeByID-{voc}.xml")
        # if not fn.exists():
        try:
            r = client.vGetNodeByIdentifier(instanceName=voc, nodeId=IDs[voc])
        except HTTPError as e:
            print(e)
        else:
            write_to_file(r.text, fn)


def test_vNodeParents():
    for voc in vocs:
        fn = Path(f"sdata/voc/parents-{voc}.xml")
        # if not fn.exists():
        try:
            r = client.vGetNodeParents(instanceName=voc, nodeId=IDs[voc])
        except HTTPError as e:
            print(e)
        else:
            write_to_file(r.text, fn)


def test_vNodeRelations():
    for voc in vocs:
        fn = Path(f"sdata/voc/relations-{voc}.xml")
        # if not fn.exists():
        try:
            r = client.vGetNodeRelations(instanceName=voc, nodeId=IDs[voc])
        except HTTPError as e:
            print(e)
        else:
            write_to_file(r.text, fn)


def test_aat_examples():
    # from a so-called online vocabulary
    write_node("ObjTechnicalTermAatVgr", 4696986)
    # manually inserted link in Beschreibung

    instanceName = "GenPlaceVgr"
    nodeId = 5091855
    write_node(instanceName, nodeId)
    # r = client.vNodeDescriptions(instanceName=instanceName,nodeId=nodeId)
    # write_to_file(r.text, "sdata/voc/nodeDescriptions-{instanceName}-{nodeId}.xml")
    r = client.vGetTermClasses(instanceName=instanceName)
    write_to_file(r.text, f"sdata/voc/termClasses-{instanceName}.xml")
    v = Vocabulary(xml=r.text)


def write_node(instanceName: str, nodeId: int):
    try:
        r = client.vGetNodeByIdentifier(instanceName=instanceName, nodeId=nodeId)
    except HTTPError as e:
        print(e)
    else:
        write_to_file(r.text, f"sdata/voc/node-{instanceName}-{nodeId}.xml")

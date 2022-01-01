from MpApi.Chunky import Chunky
from MpApi.Module import Module
from lxml import etree  # type: ignore
from typing import Union

NSMAP: dict = {"m": "http://www.zetcom.com/ria/ws/module"}

# types
since = Union[str, None]
# typed variables
baseURL: str
pw: str
user: str

with open("sdata/credentials.py") as f:
    exec(f.read())


def test_relatedItems():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    partET = etree.parse("sdata/testobjects.xml")

    relMul = c._relatedItems(part=partET, target="Multimedia")
    # toFile(relMul, "sdata/relMul.xml")
    rL = relMul.xpath(
        "//m:module[@name = 'Multimedia']/m:moduleItem[@id = '468698']",
        namespaces=NSMAP,
    )
    assert len(rL) == 1
    rL = relMul.xpath(
        "//m:module[@name = 'Multimedia']/m:moduleItem[@id = '517501']",
        namespaces=NSMAP,
    )
    assert len(rL) == 1

    relPer = c._relatedItems(part=partET, target="Person")
    # toFile(relPer, "sdata/relPer.xml")
    r = relPer.xpath(
        "count(//m:module[@name = 'Person']/m:moduleItem)", namespaces=NSMAP
    )
    assert int(r) == 1


def test_getObjects():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    partET = c._getObjects(Type="group", ID=162397, offset=0)

    itemCnt = partET.xpath(
        "count(//m:moduleItem)",
        namespaces=NSMAP,
    )
    assert int(itemCnt) == 1

    partET = c._getObjects(Type="group", ID=162397, offset=0, since=None)

    itemCnt = int(
        partET.xpath(
            "count(//m:moduleItem)",
            namespaces=NSMAP,
        )
    )
    assert itemCnt == 1

    partET = c._getObjects(Type="group", ID=162397, offset=1, since=None)

    itemCnt = int(
        partET.xpath(
            "count(//m:moduleItem)",
            namespaces=NSMAP,
        )
    )
    assert itemCnt == 1

    # print(
    # etree.tostring(partET, pretty_print=True, encoding="unicode")
    # )


def test_full():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    no = 1
    for chunk in c.getByType(ID=162397, Type="group"):
        print("before saving to file in test_chunky")
        chunk.toFile(path=f"sdata/group162397-chunk{no}.xml")
        if no == 3:
            break
        no += 1
    print("Stopping after 3")


def toFile(ET, path):
    doc = etree.ElementTree(ET)
    doc.write(path, pretty_print=True)
    print(f"Results written to {path}")

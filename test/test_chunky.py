from mpapi.constants import NSMAP, get_credentials
from mpapi.chunky import Chunky
from lxml import etree  # type: ignore

# types
since = str | None

#
# has plenty of http tests...
# pytest -sx -vv test_chunky.py


user, pw, baseURL = get_credentials()


def test_getObjects():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    m = c._getObjects(Type="group", ID=162397, offset=0)

    itemCnt = m.xpath("count(//m:moduleItem)")
    assert int(itemCnt) == 1

    m = c._getObjects(Type="group", ID=162397, offset=0, since=None)

    itemCnt = int(
        m.xpath(
            "count(//m:moduleItem)",
        )
    )
    assert itemCnt == 1

    m = c._getObjects(Type="group", ID=162397, offset=1, since=None)

    itemCnt = int(m.xpath("count(//m:moduleItem)"))
    assert itemCnt == 1


def test_relatedItems():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    partET = etree.parse("sdata/getItem-Object609717.xml")

    relMul = c._relatedItems(part=partET, target="Multimedia")
    resL = relMul.xpath(
        "//m:module[@name = 'Multimedia']/m:moduleItem[@id = '468698']",
        namespaces=NSMAP,
    )
    assert len(resL) == 1
    resL = relMul.xpath(
        "//m:module[@name = 'Multimedia']/m:moduleItem[@id = '517501']",
        namespaces=NSMAP,
    )
    assert len(resL) == 1

    relPer = c._relatedItems(part=partET, target="Person")
    # toFile(relPer, "sdata/relPer.xml")
    resL = relPer.xpath(
        "count(//m:module[@name = 'Person']/m:moduleItem)", namespaces=NSMAP
    )
    assert int(resL) == 1


def test_getByGroup():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)
    no = 1
    for chunk in c.getByType(ID=162397, Type="group"):
        # print("before saving to file in test_chunky")
        chunk.toFile(path=f"sdata/group162397-chunk{no}.xml")
        if no == 3:
            break
        no += 1
    print(" stopping after 3")


def test_getByOtherTypes():
    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw, user=user)

    todo: dict[str, int] = {
        "exhibit": 20222,  # M39
        "approval": 4460851,  # Benin
        "loc": 4220580,  # M39
    }

    for task in list(todo):
        no = 1
        for chunk in c.getByType(ID=162397, Type="group"):
            print("before saving to file in test_chunky")
            chunk.toFile(path=f"sdata/{task}{todo[task]}-chunk{no}.xml")
            if no == 3:
                break
            no += 1
        print("Stopping after 3")

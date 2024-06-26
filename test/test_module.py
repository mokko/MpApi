from mpapi.constants import NSMAP
from mpapi.module import Module
import lxml
from lxml import etree  # type: ignore
import pytest

# from mpapi.constants import get_credentials
from mpapi.client import MpApi


def test_constructors_only():
    # four different constructors, sort of
    m: MpApi.Module = Module(file="sdata/m39-join-exhibit20222.xml")
    assert m  # len(m)>0
    xml = """
    <application xmlns="http://www.zetcom.com/ria/ws/module">
        <modules>
        </modules>
    </application>
    """
    assert isinstance(m, Module)
    m = Module(xml=xml)
    assert isinstance(m, Module)
    assert len(m) == 0
    assert not (m)  # empty, so False
    ET = etree.fromstring(xml)
    m = Module(tree=ET)
    assert isinstance(m, Module)
    assert len(m) == 0
    assert not (m)
    m = Module()  # from scratch
    assert not (m)


# doesn't really belong here
def test_nsmap():
    # print(NSMAP)
    assert NSMAP["m"] is not None


def test_output():
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    m.toFile(path="sdata/output.xml")  # not sure how to test
    xml = m.toString()
    assert xml  # not sure how to test


def test_inspection():
    # requires scaffold data
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    with pytest.raises(TypeError):  # as exc_info
        m.totalSize(module="Objectssss")  # none
    assert m.totalSize(module="Exhibition") == 1
    desc = m.describe()
    # print (desc)
    assert isinstance(desc, dict)
    assert desc == {
        "Exhibition": 1,
        "Multimedia": 677,
        "Object": 194,
        "Person": 58,
        "Registrar": 194,
    }
    # print(desc)
    m.dropUUID()
    assert m.validate()


def test_iter():
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    for itemN in m:
        pass  # not sure how to test

    for itemN in m.iter(module="Multimedia"):
        pass  # itemN m.print(miN)


def test_from_scratch_interface():
    m = Module()
    moduleN = m.module(name="Object")  # setter, how to test the getter?
    moduleN = m.module(name="Object")  # setter, how to test the getter?
    moduleN = m.module(name="Multimedia")  # setter, how to test the getter?
    ET = m.toET()
    result = int(ET.xpath("count(/m:application/m:modules/m:module)", namespaces=NSMAP))
    assert result == 2
    itemN = m.moduleItem(parent=moduleN, ID=1234, hasAttachments="false")
    m.dataField(parent=itemN, name="ObjTechnicalTermClb", value="Zupftrommel")
    vrN = m.vocabularyReference(
        parent=itemN, name="ObjCategoryVoc", ID=30349, instanceName="ObjCategoryVgr"
    )
    m.vocabularyReferenceItem(parent=vrN, ID=3206642, name="Musikinstrument")
    rGrpN = m.repeatableGroup(parent=itemN, name="ObjObjectNumberGrp", size="1")
    rGrpItemN = m.repeatableGroupItem(parent=rGrpN, ID=99999998)
    rGrpItemN = m.repeatableGroupItem(parent=rGrpN)
    m.dataField(parent=rGrpItemN, name="InventarNrSTxt", value="I C 7723")
    assert m.validate()


def test_drops():
    m = Module(file="sdata/exhibit20222.xml")
    uuid = m.xpath("/m:application/m:modules/m:module/m:moduleItem/@uuid")[0]
    assert uuid == "20222"
    m.dropUUID()
    try:
        uuid = m.xpath("/m:application/m:modules/m:module/m:moduleItem/@uuid")
    except Exception:
        assert 1 == 1

    assert m.validate()


def test_join():
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    MM_before = m.totalSize(module="Multimedia")
    assert isinstance(MM_before, int)
    assert len(m) == 1124

    # first add
    ET = etree.parse("sdata/exhibit20222.xml")
    # print("1st ADD: two identical documents")
    m.add(doc=ET)
    m.toFile(path="debug.xml")
    MM_after = m.totalSize(module="Multimedia")
    assert MM_before == MM_after
    # print(len(m))
    assert len(m) == 1124

    # second add: add 2 different documents
    ET2 = etree.parse("sdata/object739673.xml")
    Obj_before = Module(tree=ET2).actualSize(module="Object")
    # print(f"{Obj_before=}")
    m.add(doc=ET2)
    assert m.totalSize(module="Object") == 195
    assert len(m) == 1125

    # there was a version where add(doc=ET) deleted most of the document, so now we
    # test that doc remains the "same"
    Obj_after = Module(tree=ET2).actualSize(
        module="Object"
    )  # ET2 has to remain the same
    assert Obj_before == Obj_after


def test_length():
    m = Module()
    assert len(m) == 0
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    assert len(m) == 1124


def test_getItem():
    m = Module(file="sdata/m39-join-exhibit20222.xml")
    # from collections import namedtuple
    # Item = namedtuple('Item', ['type', 'id'])
    itemN = m[("Multimedia", 507201)]
    # changing itemN will change m; it's not a deep copy
    assert isinstance(itemN, lxml.etree._Element)


def test_str():
    m1 = Module(file="sdata/m39-join-exhibit20222.xml")
    assert isinstance(str(m1), str)
    # print (m1.__repr__)


def test_add():
    m1 = Module(file="sdata/exhibit20222.xml")
    m2 = Module(file="sdata/exhibit20222.xml")
    m3 = m1 + m2
    m4 = Module(file="sdata/Object739673.xml")
    m5 = m3 + m4

    assert isinstance(m3, Module)
    assert len(m3) == len(m1)
    assert m3.__repr__ != m1.__repr__
    assert len(m5) == 2
    m1 = m1 + m2  # change in place
    assert len(m1) == 1
    m5 = m1 + m2 + m3  # more than 2 additions
    assert len(m5) == 1


def test_toZip():
    m1 = Module(file="sdata/exhibit20222.xml")
    m1.toZip(path="sdata/exhibit20222.xml")


def test_filter():
    # q = Search(module="Object", limit=100)
    # q.AND()
    # q.addCriterion(
    # operator="equalsField",
    # field="ObjPublicationGrp.TypeVoc",
    # value="2600647",  # Daten freigegeben für SMB-digital
    # )
    # q.addCriterion(
    # operator="equalsField",
    # field="ObjPublicationGrp.PublicationVoc",
    # value="1810139",  # Ja
    # )
    # q.addField(field="__id")
    # q.validate(mode="search") # raises on error
    # user, pw, baseURL = get_credentials()
    # client = MpApi(user=user, baseURL=baseURL, pw=pw)
    # m = client.search2(query=q)

    m = Module(file="sdata/filter-search.xml")
    new_m = m.filter(
        xpath="/m:application/m:modules/m:module/m:moduleItem[@hasAttachments = 'true']"
    )
    # write_to_file(new_m, "debug.filter.xml")
    assert len(new_m) > 5


def write_to_file(m, fn):
    print(f"Writing to file '{fn}'")
    m.toFile(path=fn)

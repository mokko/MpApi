from MpApi.Search import Search
from MpApi.Module import Module
from lxml import etree  # type: ignore
import pytest

NSMAP: dict = {"m": "http://www.zetcom.com/ria/ws/module"}


def test_constructors_only():
    # four different constructors, sort of
    m: MpApi.Module = Module(file="sdata/exhibit20222.xml")
    assert m
    xml = """
    <application xmlns="http://www.zetcom.com/ria/ws/module">
        <modules>
        </modules>
    </application>
    """
    m = Module(xml=xml)
    assert m
    ET = etree.fromstring(xml)
    m = Module(tree=ET)
    assert m
    m = Module()  # from scratch
    assert m


def test_output():
    m = Module(file="sdata/exhibit20222.xml")
    m.toFile(path="sdata/output.xml")  # not sure how to test
    xml = m.toString()
    assert xml  # not sure how to test


def test_inspection():
    m = Module(file="sdata/exhibit20222.xml")
    with pytest.raises(TypeError) as exc_info:
        m.totalSize(module="Object")  # none
    assert m.totalSize(module="Multimedia") == 619
    desc = m.describe
    print(desc)  # todo write a good test
    m.dropUUID()
    assert m.validate()


def test_iter():
    m = Module(file="sdata/exhibit20222.xml")
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
    rGrpItemsL = m.repeatableGroupItems(parent=rGrpN)
    rGrpItemN = m.repeatableGroupItemAdd(parent=rGrpN, ID=99999998)
    m.dataField(parent=rGrpItemN, name="InventarNrSTxt", value="I C 7723")
    assert m.validate()


def test_drops_other_changes():
    m = Module(file="sdata/exhibit20222.xml")
    m.dropUUID()
    # ... TODO: some methods are missing
    assert m.validate()


def test_join():
    m = Module(file="sdata/exhibit20222.xml")
    before = m.totalSize(module="Multimedia")
    assert isinstance(before, int)
    ET = etree.parse("sdata/exhibit20222.xml")
    m.add(doc=ET)
    after = m.totalSize(module="Multimedia")
    assert before == after
    ET2 = etree.parse("data/739673.xml")
    xml = len(etree.tostring(ET2, pretty_print=True, encoding="unicode"))
    m.add(doc=ET2)
    assert m.totalSize(module="Object") == 1
    # there was a version where add(doc=ET) deleted most of the document, so now we
    # test that doc remains the same
    xml2 = len(etree.tostring(ET, pretty_print=True, encoding="unicode"))
    # assert xml == xml2 # len()?
    print(ET2)

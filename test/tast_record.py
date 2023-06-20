from mpapi.module import Module
from mpapi.record import Record
import lxml

# from lxml import etree  # type: ignore
import pytest


#
# obsolete
#

def test_constructors_only():

    m: MpApi.Module = Module(file="sdata/getItem-Object993084.xml")
    assert m  # len(m)>0

    r = Record(m)
    assert r


def test_read():
    m = Module(file="sdata/getItem-Object993084.xml")
    r = Record(m)
    orgUnit = r.read(field="__orgUnit")
    assert orgUnit.text == "EMSudundSudostasien"

    sachbegriff = r.read(field="ObjTechnicalTermClb")
    assert sachbegriff.text == "Schalenhalslaute"

    objTyp = r.read(field="ObjCategoryVoc")
    print(f"objTyp {objTyp.text}")
    assert objTyp.text == "Musikinstrument"

    objObjectNumberGrp = r.read(field="ObjObjectNumberGrp")
    print(f"rGrpN {objObjectNumberGrp}")
    assert isinstance(objObjectNumberGrp, lxml.etree._Element)

    InventarNrSTxt = r.read(field="ObjObjectNumberGrp.InventarNrSTxt")
    print(f"InvNrS {InventarNrSTxt.text}")
    assert InventarNrSTxt.text == "I C 7703"

    identNrQuali = r.read(field="ObjObjectNumberGrp.DenominationVoc")
    print(f"identNrQuali '{identNrQuali.text}'")
    assert identNrQuali.text == "Ident. Nr."

    # todo
    # test that it raises if field does not exist


def test_create():
    xml = """
    <application xmlns="http://www.zetcom.com/ria/ws/module">
        <modules>
            <module name="Object">
                <moduleItem id="993084"/>
            </module>
        </modules>
    </application>"""

    m = Module(xml=xml)
    r = Record(m)
    r.create(field="__orgUnit", value="EMMusikethnologie")
    m2 = r.toModule()
    orgUnitN = m2.xpath(
        """/m:application/m:modules/m:module/m:moduleItem/m:systemField[
        @name = '__orgUnit'
    ]/m:value"""
    )[0]
    assert orgUnitN.text == "EMMusikethnologie"

    """
    <dataField dataType="Clob" name="ObjTechnicalTermClb">
      <value>Schalenhalslaute</value>
    </dataField>
    """
    r.create(field="ObjTechnicalTermClb", value="Schalenhalslaute")
    print("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    print(r)


def test_update():
    m = Module(file="sdata/getItem-Object993084.xml")
    r = Record(m)
    r.update(field="__orgUnit", value="EMMusikethnologie")
    m2 = r.toModule()
    orgUnitN = m2.xpath(
        """/m:application/m:modules/m:module/m:moduleItem/m:systemField[
        @name = '__orgUnit'
    ]/m:value"""
    )[0]
    print(f"orgUnitN {orgUnitN}")
    m2.toFile(path="debug.xml")
    assert orgUnitN.text == "EMMusikethnologie"


def test_delete():
    pass

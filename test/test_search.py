"""
Test the Search module
"""

from mpapi.search import Search
import pytest


one = """
<application xmlns="http://www.zetcom.com/ria/ws/module/search" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
             xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd">
    <modules>
        <module name="Object">
            <search limit="-1" offset="0">
                <expert>
                    <and>
                        <equalsField fieldPath="ObjCurrentLocationVoc" operand="4220560"/>
                        <notEqualsField fieldPath="__orgUnit" operand="EMPrimarverpackungen"/>
                        <notEqualsField fieldPath="__orgUnit" operand="AKuPrimarverpackungen"/>
                    </and>
                </expert>
            </search>
        </module>
    </modules>
</application>
"""

two = """
<application xmlns="http://www.zetcom.com/ria/ws/module/search" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
             xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd">
    <modules>
        <module name="Object">
            <search limit="-1" offset="0">
                <expert>
                    <and>
                        <equalsField fieldPath="ObjCurrentLocationVoc" operand="4220560"/>
                        <notEqualsField fieldPath="__orgUnit" operand="EMPrimarverpackungen"/>
                        <notEqualsField fieldPath="__orgUnit" operand="AKuPrimarverpackungen"/>
                        <not>
                            <contains fieldPath="ObjTextOnlineGrp.TextHTMLClb" operand="SM8HF"/>
                        </not>
                    </and>
                </expert>
            </search>
        </module>
    </modules>
</application>
"""


def test_validate():
    # print(one)
    s = Search(fromString=one)
    assert s.validate(mode="search") is True


def test_validate2():
    s = Search(fromString=two)
    assert s.validate(mode="search") is True


def test_single_criterion():
    s = Search(module="Object")
    s.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    assert s.validate(mode="search") is True


def test_multiple_criteria():
    s = Search(module="Object")
    s.AND()
    s.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
        value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
    )

    assert s.validate(mode="search") is True


def test_five():
    s = Search(module="Object")
    s.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    s.AND()
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
        value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
    )

    with pytest.raises(Exception):
        s.validate(mode="search")


def test_AND_and_NOT():
    s = Search(module="Object")
    s.AND()
    s.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
        value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
    )
    s.NOT()
    s.addCriterion(
        operator="contains",
        field="ObjTextOnlineGrp.TextHTMLClb",
        value="SM8HF",
    )
    # s.print()
    s.toFile(path="search.tmp.xml")
    assert s.validate(mode="search") is True


def test_with_field():  # addField
    s = Search(module="Object")
    s.AND()
    s.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    s.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
        value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
    )
    s.NOT()
    s.addCriterion(
        operator="contains",
        field="ObjTextOnlineGrp.TextHTMLClb",
        value="SM8HF",
    )
    s.addField(field="__id")
    # s.print()
    s.toFile(path="search.tmp.xml")
    assert s.validate(mode="search") is True


def test_attributes():
    # attributes are limit and offset
    q = Search(module="Object")
    q.AND()
    q.addCriterion(
        operator="equalsField",
        field="ObjCurrentLocationVoc",
        value="4220560",  # O1.189.01.K1 M13
    )
    q.addCriterion(
        operator="notEqualsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    assert q.offset() == 0
    q.offset(value="123")
    assert q.offset(value="123")
    assert q.limit() == -1
    q.limit(value=10)
    assert q.limit() == 10


def test_equals_exact():
    # trying out equalsExact
    q = Search(module="Object")
    q.addCriterion(
        operator="equalsExact",
        field="__id",
        value="2165",
    )
    assert q.validate(mode="search") is True


def test_exists():
    q = Search(module="Object")
    q.AND()
    q.addCriterion(
        operator="equalsField",  # notEqualsTerm
        field="__orgUnit",
        value="EMMusikethnologie",  # 1632806EM-Primärverpackungen
    )
    q.exists(field="ObjPublicationGrp")
    q.AND()
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # use id? Daten freigegeben für SMB-digital
    )
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.PublicationVoc",
        value="1810139",  # Ja
    )
    q.endConjunction()
    q.toFile(path="debug.exists.xml")

    assert q.validate(mode="search") is True

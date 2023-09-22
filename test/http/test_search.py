from mpapi.search import Search
from mpapi.constants import get_credentials
from mpapi.client import MpApi
from mpapi.module import Module

user, pw, baseURL = get_credentials()
client = MpApi(baseURL=baseURL, user=user, pw=pw)


def test_equals_exact():
    # trying out equalsExact
    q = Search(module="Object")
    q.addCriterion(
        operator="equalsExact",
        field="ObjObjectNumberTxt",
        value="V A 1934",
    )
    assert q.validate(mode="search") is True
    m = client.search2(query=q)
    fn = "debug.V A 1934.xml"
    print(f"Writing to {fn}...")
    m.toFile(path=fn)


def test_exists():
    q = Search(module="Object", limit=10)
    q.AND()
    q.addCriterion(
        operator="equalsField",  # notEqualsTerm
        field="__orgUnit",
        value="EMMusikethnologie",
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
    # q.endConjunction()
    q.toFile(path="debug.exists.xml")

    assert q.validate(mode="search") is True

    print("Launching test.exist search")
    m = client.search2(query=q)
    fn = "debug.exists.data.xml"
    print(f"Writing to {fn}...")
    m.toFile(path=fn)

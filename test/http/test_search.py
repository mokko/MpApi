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
    print (f"Writing to {fn}...")
    m.toFile(path=fn)


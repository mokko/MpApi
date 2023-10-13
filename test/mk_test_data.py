#
# Little script that d/l the test data
#

from pathlib import Path
from mpapi.constants import get_credentials
from mpapi.module import Module
from mpapi.search import Search
from mpapi.client import MpApi

user, pw, baseURL = get_credentials()


def get_m39(c) -> None:
    """
    What we need is the join file from mink
    mink -j m39
    jobs.dsl
    m39:
        getPack exhibit 20222 m39
    m39-join-exhibit20222.xml
    """
    fn = Path("sdata/m39-join-exhibit20222.xml")
    if not fn.exists():
        raise TypeError("File missing")


def get_item(c, mtype: str, ID: int) -> None:
    # if mtype not in allowed_types:
    #    raise SyntaxError("Unknown type")
    ID = int(ID)

    if mtype == "Exhibition":
        mtype2 = "exhibit"
    else:
        mtype2 = mtype

    fn = Path(f"sdata/{mtype2}{ID}.xml")
    if not fn.exists():
        m = c.getItem2(mtype=mtype, ID=ID)
        print(f"Writing to {fn}")
        m.toFile(path=fn)


def filter_search(c):
    fn = "sdata/filter-search.xml"
    if not Path(fn).exists():
        print("filter search with limit 100...")
        q = Search(module="Object", limit=100)
        q.AND()
        q.addCriterion(
            operator="equalsField",
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # Daten freigegeben für SMB-digital
        )
        q.addCriterion(
            operator="equalsField",
            field="ObjPublicationGrp.PublicationVoc",
            value="1810139",  # Ja
        )
        q.addField(field="__id")
        q.validate(mode="search")  # raises on error
        m = c.search2(query=q)
        print(f"Writing {fn}")
        m.toFile(path=fn)


if __name__ == "__main__":
    c = MpApi(baseURL=baseURL, pw=pw, user=user)
    print(f"Logging in as '{user}'")
    if not Path("sdata"):  # assuming we execute in MpApi/test
        Path.mkdir()
    get_item(c, "Exhibition", 20222)
    get_m39(c)
    get_item(c, "Object", 739673)
    filter_search(c)

"""
Low-level API request to get all SMB approved records
"""

from pathlib import Path
from mpapi.search import Search
from mpapi.client import MpApi
from mpapi.module import Module

# provides baseURL, pw and user
credentials = "credentials.py"
if Path(credentials).exists():
    with open(credentials) as f:
        exec(f.read())

if __name__ == "__main__":
    client = MpApi(baseURL=baseURL, user=user, pw=pw)

    q = Search(module="Object")
    q.AND()
    q.addCriterion(
        operator="equalsField",  # notEqualsTerm
        field="ObjPublicationGrp.TypeVoc",
        value=str(2600647),  # "Daten freigegeben für SMB-Digital"
    )
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.PublicationVoc",
        value=str(1810139),  # Ja
    )

    q.validate(mode="search")
    print("Query validates, about to launch query")
    # q.toFile(path="query.xml")
    q.addField(field="__id")

    m = client.search2(query=q)
    print("Saving query to response.xml")
    m.toFile(path="response.xml")

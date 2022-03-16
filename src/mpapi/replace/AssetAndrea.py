"""
Andrea wants to publish a group on SMB-Digital; this script SMB approves all 
assets attached to object records in that group, unless they have 
    SMB-Freigabe = Nein
For a couple secret Yurupari flutes, photos/depictions are not shown.

Fotografen:
look for assets
- Bereich "EM-Am Ethnologie" -> EMAmEthnologie 
- only assets that dont have SMB-Freigabe yet
- belong to objects in group 29636
do
- set SMBFreigabe for those assets

"""

import datetime

from mpapi.search import Search
from mpapi.replace.AssetFreigabe import AssetFreigabe


class AssetAndrea(AssetFreigabe):
    def search(self, Id, limit=-1):
        query = Search(module="Multimedia", limit=limit)
        query.AND()
        # 1st criteria
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="EMAmEthnologie",
        )

        # 2nd criteria
        query.addCriterion(
            operator="equalsField",
            field="MulObjectRef.ObjObjectGroupsRef.__id",
            value="29636",  # Andreas Gruppe
        )

        # 3rd criteria
        query.addCriterion(
            operator="notEqualsField",  # equalsTerm
            field="MulApprovalGrp.TypeVoc",  # ObjCurrentLocationVoc
            value="1816002",  # using vocId SMB-Digital = 1816002
        )
        print(query.toFile(path="query.xml"))
        query.validate(mode="search")
        return query

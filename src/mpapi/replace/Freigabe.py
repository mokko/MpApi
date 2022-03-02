import datetime
from mpapi.search import Search
from mpapi.replace.WestFreigabe import WestFreigabe


class Freigabe(WestFreigabe):
    def Input(self):
        groups = {  # Wechsel 2022-03
            "M42W": "181396",
            "M44W": "179396",
            "M45W": "181397",
            "M45Wii": "179397",
        }
        return groups

    def search(self, Id, limit=-1):
        """
        We're trying to find exactly the right records in one go.
        - Objects at are members in certain groups
        - Objects that are not SMBfreigegeben yet

        Nicht freigegeben can be expressed in two ways SMBFreigabe = No or no SMBFreigabe
        in any case we leave records alone that have SMBFreigabe already.
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=Id,  # using voc id
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # use id? Daten freigegeben für SMB-digital
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="__orgUnit",
            value="AKuPrimarverpackungen",  # 1632806EM-Primärverpackungen
        )
        query.addField(field="ObjPublicationGrp")
        query.addField(field="ObjPublicationGrp.repeatableGroupItem")
        query.addField(field="ObjPublicationGrp.PublicationVoc")
        query.addField(field="ObjPublicationGrp.TypeVoc")
        # query.print()
        return query

    def onItem(self):
        """
        I cant decide if I should run independent jobs for the marker and for
        SMB Freigabe or everything should be in one thing.

        for every identified record, set SMBFreigabe
        """
        return self.setObjectFreigabe  # returns a callback

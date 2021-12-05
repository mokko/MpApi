from lxml import etree
from MpApi.Module import Module
from MpApi.Search import Search

"""
Touch Replace Plugin

==Problem==
If a multimedia record is smb approved, but the linked object record is not updated,
recherche.smb doesn't show the multimedia asset. 

In order to show it, we manually update the record (e.g. by adding and deleting a 
space in the object record) which triggers the update of the record with the asset on 
recherche.smb. 

==Workaround==
Obviously, the recherche.smb update mechanism should be cleverer, but until this happens
I suggest a workaround where we automate the manual update using this update script.

==Pseudo-Algorithm==

First find the object records whose smb-approved assets have a newer last-edit-date than
the object record. Then update the last-edit record.

It is possible that touch does not fit the requirements of a replace plugin.

For every object record we need to get the smb-approved mulimedia records and compare 
their last change date.

So should we loop thru the objects marked with SM8HF? Or should we loop thru the objects
at a certain location? Probably the latter b/c that is more sustainable.

==Scope==
For the time being, we only do this for HF Objects, but in the future we can do it for 
all object records which have a smb approval.

Why touch?
	"touch is a command used to update the access date and/or modification date of a 
	computer file or directory."
	source: https://en.wikipedia.org/wiki/Touch_(command)
"""


class WestMarker:
    def input(self):
        STO = {
            # Westflügel, Westspange Eröffnung
            "O1.189.01.K1-M13": "4220560",
            "O2.017.B2-M37": "4220571",
            "O2.019.P3-M39": "4220580",
            "O2.029.B3-M15": "4220589",
            "O2.037.B3-M16": "4220679",
            "O2.124.K1-M14": "4220743",
            "O2.133.K2-M12": "4220744",
            "O2.160.02.B2-SMAfrika": "4220747",
            "O3.014.B2-M61": "4220964",
            "O3.021.B3-M44": "4220994",
            "O3.090.K1-M43StuSamZ-Asien": "4221084",
            "O3.097.K2-M42": "4221123",
            "O3.125.02.B2-M60": "4221168",
            "O3.126.P3-M62": "4221189",
            "O3.127.01.B3-M45": "4221214",
        }
        r = {"M39locId": "4220580"}  # for testing
        return STO

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def search(self, Id, limit=-1):
        """
        We're trying to find exactly the right records in one go.
        - Objects at a certain locationId
        - Objects that are not SMBfreigegeben yet
        whether they have marker or not is irrelevant

        Nicht freigegeben can be expressed in two ways SMBFreigabe = No or no SMBFreigabe
        in any case we leave records alone that have SMBFreigabe already.
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjCurrentLocationVoc",
            value=Id,  # using voc id
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
        # query.NOT()
        # query.addCriterion( # doesn't find records without ObjTextOnlineGrp, while "enthält nicht" in the Gui does find empty records
        #    operator="contains",
        #    field="ObjTextOnlineGrp.TextHTMLClb",
        #    value="SM8HF",
        # )
        # query.OR()
        # then we have to download all records and test them manually
        query.addField(field="ObjTextOnlineGrp.repeatableGroupItem")
        query.addField(field="ObjTextOnlineGrp.TextHTMLClb")
        query.addField(field="ObjTextOnlineGrp.TextClb")
        # query.print()
        return query

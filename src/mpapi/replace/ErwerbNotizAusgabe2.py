import datetime
import importlib
from lxml import etree
from Search import Search
from Module import Module
import re
from mpapi.replace.ErwerbNotizAusgabe import ErwerbNotizAusgabe

"""
 Loop thru the SMB-freigegebenen objects of one Bereich and write erwerbNotizAusgabe
 if there is none already, using the data from various fields
"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class ErwerbNotizAusgabe2(ErwerbNotizAusgabe):  # inheritance!
    def Input(self):
        STO = {
            "Musikethnologie": "EMMusikethnologie",
        }
        return STO

    def search(self, Id, limit=-1):
        """
        We want object records without ErwerbNotizAusgabe (i.e. empty)

        It seems impossible to select all records without ErwerbNotizAusgabe in RIA and
        exactly those. I can only get records with any ErwerbNotiz entry that don't have
        any entries with the type Ausgabe, not records without any ErwerbNotiz entries.

        Typ (Erwerb. Notiz)->ist nicht gleich: Ausgabe
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # 2600647 = Daten freigegeben für SMB-digital
        )
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="ObjPublicationGrp.PublicationVoc",
            value="1810139",  # 1810139 = Ja
        )
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="EMMusikethnologie",  # 1632806EM-Primärverpackungen
        )
        # We need full records, so no fields here
        # query.print()
        return query

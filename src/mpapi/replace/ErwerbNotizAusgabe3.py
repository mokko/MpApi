import datetime
import importlib
from lxml import etree
from Search import Search
from Module import Module
import re
from Replace.ErwerbNotizAusgabe import ErwerbNotizAusgabe

"""
 Loop thru the objects of one group and write erwerbNotizAusgabe
 if there is none already, using the data from various fields
"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class ErwerbNotizAusgabe3(ErwerbNotizAusgabe):  # inheritance!
    def Input(self):
        STO = {
            "BoxerGroup": "117396",
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
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=Id,  # using voc id
        )
        # We need full records, so no fields here
        # query.print()
        return query

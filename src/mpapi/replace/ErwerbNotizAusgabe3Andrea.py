import datetime
import importlib
from lxml import etree
from mpapi.search import Search
from mpapi.module import Module
from mpapi.replace.ErwerbNotizAusgabe import ErwerbNotizAusgabe
import re

# from Replace.ErwerbNotizAusgabe import ErwerbNotizAusgabe

"""
 Loop thru the objects of one group and write erwerbNotizAusgabe
 if there is none already, using the data from various fields
"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class ErwerbNotizAusgabe3Andrea(ErwerbNotizAusgabe):  # inheritance!
    def Input(self):
        groups = {
            "Andrea": "29636",
        }
        return groups

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
            value=Id,
        )
        # We need full records, so no fields here
        # query.print()
        return query

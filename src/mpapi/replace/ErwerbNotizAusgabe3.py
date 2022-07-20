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


class ErwerbNotizAusgabe3(ErwerbNotizAusgabe):  # inheritance!
    def Input(self):
        groups = {
            # "M42W": "181396",
            # "M44W": "179396",
            # "M45W": "181397",
            # "M45Wii": "179397",
            # "M22": "250398",
            # "M24": "250400",
            # "M21": 250397  # is int now, used to be str
            # "M26": 250402,
            # "m51": 26816,
            # "m52": 29032,
            # "m23": 250399
            # "m29/30": 250396
            # "E57010" : 29583,
            # "E57020" :29584,
            # "E57030": 29585,
            # "E57040" : 29586,
            # "E57050" : 29587,
            # "E57060" : 29588,
            # "E57080" : 29589,
            # "E57140" : 29590,
            # "E57150" : 29591,
            # "E57160" : 29592,
            # "E57170" : 29593,
            # "E57180" : 29594,
            # "E57190" : 29595,
            # "E57200" : 29596,
            # "E57210" : 29597,
            # "E57220" : 29598,
            # "E57230" : 29599,
            # "E57240" : 29600,
            # "E57470" : 29601,
            # "E57480" : 29602,
            # "E57490" : 29551,
            # "RA275" : 29603
            "M27Amazonas": 292398
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
            value=str(Id),  # using voc id
        )
        # We need full records, so no fields here
        # query.print()
        return query

import datetime
from lxml import etree
from mpapi.search import Search
from mpapi.module import Module
from mpapi.replace.ErwerbNotizAusgabe import ErwerbNotizAusgabe
import re
from typing import Any, Callable

"""
Die Version 4 soll alle Objekte einer Ausstellung ändern

Für die HFObjekte wollen wir ErwerbNotizAusgabe befüllen.
Wir ändern ErwerbNotizAusgabe, nur wenn das Feld leer ist.
Wir schreiben Inhalte aus anderen Feldern rein. XSLT jetzt in Python reimplementiert.

Typische Fehlermeldungen des Clients
400 Client Error: Bad Request for url

"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ET = Any


class ErwerbNotizAusgabe4(ErwerbNotizAusgabe):
    def Input(self):
        STO = {
            "WAF18": 23626,
            "WAF20": 23466,
            "WAF3132": 252804,
            "WAF55": 23545,
            "WAF58": 24124,
        }
        return STO

    def search(self, Id, limit=-1):
        """
        We want object records without ErwerbNotizAusgabe (i.e. empty)

        It seems impossible to select all records without ErwerbNotizAusgabe and
        exactly those in RIA. I can only get records with any ErwerbNotiz entry
        that don't have any entries with the type Ausgabe, not records without
        any ErwerbNotiz entries.

        Typ (Erwerb. Notiz)->ist nicht gleich: Ausgabe
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjRegistrarRef.RegExhibitionRef.__id",
            value=str(Id),  # using voc id
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
        # doesn't reliably find all records without ObjAcquisitionNotesGrp
        # query.addCriterion(
        # operator="notEqualsField",  # notEqualsTerm id 1805533 für Ausgabe
        # field="ObjAcquisitionNotesGrp.TypeVoc",
        # value="Ausgabe",  #
        # )
        # We need full records, so no fields here
        # query.print()
        return query

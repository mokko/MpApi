import datetime
from lxml import etree
from Search import Search
from Module import Module
import re

"""
Für die HFObjekte wollen wir ErwerbNotizAusgabe befüllen.
Wir ändern ErwerbNotizAusgabe nur wenn das Feld leer ist.
Wir schreiben Inhalte aus anderen Feldern rein. XSLT jetzt in Python reimplementiert.

Typische Fehlermeldungen des Clients
400 Client Error: Bad Request for url

"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class ErwerbNotizAusgabe:
    def input(self):
        STO = {
            # Westflügel, Westspange Eröffnung
            "O1.189.01.K1 M13": "4220560",
            "O2.017.B2 M37": "4220571",
            "O2.019.P3 M39": "4220580",
            "O2.029.B3 M15": "4220589",
            "O2.037.B3 M16": "4220679",
            "O2.124.K1 M14": "4220743",
            "O2.133.K2 M12": "4220744",
            "O2.160.02.B2 SM Afrika": "4220747",
            "O3.014.B2 M61": "4220964",
            "O3.021.B3 M44": "4220994",
            "O3.090.K1 M43StuSamZ-Asien": "4221084",
            "O3.097.K2 M42": "4221123",
            "O3.125.02.B2 M60": "4221168",
            "O3.126.P3 M62": "4221189",
            "O3.127.01.B3 M45": "4221214",
        }
        return STO

    def loop(self):
        """
        loop thru objects in the results
        """
        moduleType = "Object"
        return f"/m:application/m:modules/m:module[@name = '{moduleType}']/m:moduleItem"

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
        # doesn't reliably find all records without ObjAcquisitionNotesGrp
        # query.addCriterion(
        # operator="notEqualsField",  # notEqualsTerm id 1805533 für Ausgabe
        # field="ObjAcquisitionNotesGrp.TypeVoc",
        # value="Ausgabe",  #
        # )
        # We need full records, so no fields here
        # query.print()
        return query

    def onItem(self):
        # just return the callback
        return self.erwerbNotiz

    # --------------------
    # STUFF             -
    # --------------------

    def erwerbNotiz(self, *, itemN, user):
        """
        Just check conditions and transparently trigger correct method
        itemN should be a different moduleItem every time it gets called
        """
        moduleItemId = itemN.xpath("@id")[0]
        # count = itemN.xpath("count(//m:moduleItem)", namespaces=NSMAP)
        # print (f"RCOUNT: {count} inside erwerbNotiz; should be 1")

        rGrpL = itemN.xpath(
            "m:repeatableGroup[@name='ObjAcquisitionNotesGrp']", namespaces=NSMAP
        )

        if len(rGrpL) > 0:
            # Some kind of Erwerb.Notiz exists
            grpItemL = rGrpL[0].xpath(
                "m:repeatableGroupItem[m:vocabularyReference/@name = 'TypeVoc' and ./m:vocabularyReference/m:vocabularyReferenceItem/m:formattedValue = 'Ausgabe']",
                namespaces=NSMAP,
            )
            if len(grpItemL) > 0:
                print(" ErwerbNotizAusgabe exists already -> do nothing")
            else:
                # there should always only be one ObjAcquisitionNotes Grp
                print(
                    "ErwerbNotiz exists already, but no Ausgabe -> createErwerbNotizAusgabe"
                )
                return self.createErwerbNotizAusgabe(Id=moduleItemId, itemN=itemN)
        else:
            print(" ErwerbNotiz doesn't exist yet -> createErwerbNotizAusgabe")
            return self.createErwerbNotizAusgabe(Id=moduleItemId, itemN=itemN)

    def createErwerbNotizAusgabe(self, *, Id, itemN):
        """
        The Id we get is from moduleItem.
        itemN is the whole moduleItem node

        We keep existing repeatableGroupItems in ObjAcquisitionNotesGrp and add a new
        repeatableGroupItem for erwerbNotizAusgabe.

        If there is no ErwerbNotiz, so we're making a completely new one.
        If there is no ErwerbNotizAusgabe, we're making one.
        If there is an ErwerbNotizAusgabe, we dont get here.

        <repeatableGroupItem id="40926665">
            <dataField dataType="Clob" name="MemoClb">
              <value>Eingang 2004, Inventarisiert 2006</value>
            </dataField>
            <dataField dataType="Long" name="SortLnu">
              <value>1</value>
            </dataField>
            <vocabularyReference name="TypeVoc" id="62641" instanceName="ObjAcquisitionNotesTypeVgr">
              <vocabularyReferenceItem id="1805535" name="Notiz">
              </vocabularyReferenceItem>
            </vocabularyReference>
        </repeatableGroupItem>

        id 212110

        <repeatableGroup name="ObjAcquisitionNotesGrp" size="3">
          <repeatableGroupItem id="40858269">
            <dataField dataType="Clob" name="MemoClb">
              <value>Rückführung Wiesbaden</value>
            </dataField>
            <dataField dataType="Long" name="SortLnu">
              <value>1</value>
              <formattedValue language="en">1</formattedValue>
            </dataField>
            <vocabularyReference name="TypeVoc" id="62641" instanceName="ObjAcquisitionNotesTypeVgr">
              <vocabularyReferenceItem id="1805535" name="Notiz">
                <formattedValue language="en">Notiz</formattedValue>
              </vocabularyReferenceItem>
            </vocabularyReference>
          </repeatableGroupItem>
          <repeatableGroupItem id="49996972">
            <dataField dataType="Clob" name="MemoClb">
              <value>16. Jh., im Auftrag von Oba Esigie (reg. 1517-1550) oder seines Sohnes Oba Orhogbua (reg. 1550-1570), Königspalast, Benin-Stadt; durch Erbschaft an Oba Ovonramwen (ca. 1857-1914; reg. 1888-97), Königspalast, Benin-Stadt; geplündert im Zusammenhang mit der britischen Eroberung von Benin, 1897; in unbekanntem Besitz nach der Eroberung des Königreichs Benin; gesammelt im Auftrag der Firma Bey &amp; Co., zwischen 1897 und 1898 im Gebiet des späteren kolonialen Nigeria; verkauft an das Königliche Museum für Völkerkunde in Berlin, 1899.</value>
            </dataField>
            <dataField dataType="Long" name="SortLnu">
              <value>5</value>
              <formattedValue language="en">5</formattedValue>
            </dataField>
            <vocabularyReference name="TypeVoc" id="62641" instanceName="ObjAcquisitionNotesTypeVgr">
              <vocabularyReferenceItem id="1805533" name="Ausgabe">
                <formattedValue language="en">Ausgabe</formattedValue>
              </vocabularyReferenceItem>
            </vocabularyReference>
          </repeatableGroupItem>
        </repeatableGroup>
        """

        note = self.writeNote(itemN=itemN)
        if note is None or note == "":
            print(" Satz is empty -> not adding anything")
            return

        module = "Object"
        outer = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
            <modules>
                <module name="{module}">
                    <moduleItem id="{Id}">
                        <repeatableGroup name="ObjAcquisitionNotesGrp"/>
                    </moduleItem>
                </module>
            </modules>
        </application>
        """

        ET = etree.fromstring(outer)

        newItem = f"""
            <repeatableGroupItem xmlns="http://www.zetcom.com/ria/ws/module">
                <dataField dataType="Clob" name="MemoClb">
                  <value>{note}</value>
                </dataField>
                <dataField dataType="Long" name="SortLnu">
                  <value>1</value>
                </dataField>
                <vocabularyReference name="TypeVoc" id="62641" instanceName="ObjAcquisitionNotesTypeVgr">
                  <vocabularyReferenceItem id="1805533"/>
                </vocabularyReference>
            </repeatableGroupItem>
        """

        newET = etree.fromstring(newItem)
        rpGrpN = ET.xpath("//m:moduleItem/m:repeatableGroup", namespaces=NSMAP)[0]
        rpGrpN.append(newET)  # add new ErwerbNotiz (Ausgabe)

        doc = etree.ElementTree(ET)
        doc.write("debug.xml", pretty_print=True, encoding="UTF-8")
        xml = etree.tostring(
            ET, pretty_print=True, encoding="unicode"
        )  # dont return bytes
        xml = xml.encode()  # force UTF8

        m = Module(tree=ET)
        # print (" about to validate")
        m.validate()

        # print (f"xml:{xml}")

        payload = {
            "type": "createRepeatableGroup",  # is actual creating a repeatableGroupItem
            "module": module,
            "id": Id,
            "repeatableGroup": "ObjAcquisitionNotesGrp",
            "xml": xml,
            "success": f"{module} {Id}: update ErwerbNotizAusgabe {note}",
        }
        return payload

    def writeNote(self, *, itemN):
        """
        node carries the whole moduleItem as etree.
        returns the new text for ErwerbNotizAusgabe

        Originally, I wanted to use xslt here. But now it's easier to re-implmenent the logarithm
        in Python using lxml than to use saxon from Python xslt2 even if that means extra debugging.
        """

        moduleItemId = itemN.xpath("@id")[0]
        # count = itemN.xpath("count(//m:moduleItem)", namespaces=NSMAP)
        # print (f"COUNT: {count} in writeNote; should be 1")
        part = {}

        part["art2"] = self._xText(
            node=itemN,
            select="""m:repeatableGroup[@name='ObjAcquisitionMethodGrp']/m:repeatableGroupItem
            /m:vocabularyReference/m:vocabularyReferenceItem/m:formattedValue
            """,
        )

        part["dateFromTxt"] = self._xText(
            node=itemN,
            select="""m:repeatableGroup[
                @name = 'ObjAcquisitionDateGrp']/m:repeatableGroupItem/m:dataField[
                @name = 'DateFromTxt']/m:value
            """,
        )

        part["dateTxt"] = self._xText(
            node=itemN,
            select="""m:repeatableGroup[
                @name = 'ObjAcquisitionDateGrp']/m:repeatableGroupItem/m:dataField[
                @name = 'DateTxt']/m:value)
            """,
        )

        part["ErwerbNotizErwerbungVon"] = self._xText(
            node=itemN,
            select="""m:repeatableGroup[
				@name = 'ObjAcquisitionNotesGrp']/m:repeatableGroupItem[
				m:vocabularyReference/m:vocabularyReferenceItem/m:formattedValue = 'Erwerbung von']/m:dataField/m:value
            """,
        )

        part["PKVeräußerer"] = itemN.xpath(
            """substring-before(m:moduleReference[
                @name = 'ObjPerAssociationRef']/m:moduleReferenceItem[
                    m:vocabularyReference/m:vocabularyReferenceItem/m:formattedValue = 'Veräußerer'
                ]/m:formattedValue, ' (')
            """,
            namespaces=NSMAP,
        )
        if part["PKVeräußerer"] == "":
            part["PKVeräußerer"] = None

        # Vorbesitzer is irrelevant as it is uncertain if this relates to Erwerbszusammenhang

        #
        # MAPPING, FRAGMENTS AND CONCLUSIONS
        #
        adict = {
            "source": "target",
            "unbekannter Zugang (Expedition)": "unbekannte Zugangsart (Expedition)",
            "Zugang ungeklärt": "ungeklärte Zugangsart",
            "Unbekannt": "unbekannte Erwerbungsart",
        }

        deadOrPermission = [
            "Evaristo Muyinda",
            "Gerd Koch",
            "Internationales Institut für Traditionelle Musik",
            "Koch, Gerd",
        ]

        if part["dateTxt"] is not None:
            part["datum"] = part["dateTxt"]
        else:
            part["datum"] = part["dateFromTxt"]

        if part["datum"] is not None:
            part["datum"] = part["datum"].strip()

        if part["datum"] is not None:
            datum = part["datum"]
            p = re.compile("(\d\d\d\d)$")
            m = p.search(datum)
            if m:
                part["jahr"] = int(m.group(1))
            else:
                part["jahr"] = 99999

            p = re.compile("\d+\.\d+\.\d\d\d\d")
            m = p.search(datum)
            if m:
                part["datum2"] = f"am {datum}"
            elif re.search(r" \(um\)", datum):
                before = datum.split("(")[0].strip
                part["datum2"] = f" um {before}"
                part["jahr"] = int(before)  # not safe
            elif re.search(r"\(\?\)", datum):
                before = datum.split("(")[0].strip
                part["datum2"] = before + " Datum fraglich"
                part["jahr"] = int(before)  # not safe
            else:
                part["datum2"] = datum
        else:
            part["datum2"] = None
            part["jahr"] = 99999

        try:
            part["art"] = adict["art2"]
        except:
            part["art"] = part["art2"]

        if part["art"] is not None:
            part["art"] = part["art"].strip()

        if part["PKVeräußerer"] is not None:
            part["von"] = part["PKVeräußerer"]
        else:
            part["von"] = part["ErwerbNotizErwerbungVon"]

        if part["von"] is not None:
            part["von"] = part["von"].strip()

        satz = ""
        if part["art"] is not None:
            satz = part["art"]
        if part["von"] is not None:
            if part["jahr"] <= 1950 or part["von"] in deadOrPermission:
                if satz != "":
                    satz += " "
                satz += f"von {part['von']}"
        if part["datum2"] is not None:
            if satz != "":
                satz += " "
            else:  # wenn keine Zugangsart und keine Veräußerer
                satz = "Zugang "
            satz += f"{part['datum2']}"

        part["satz"] = satz.strip()

        # https://stackoverflow.com/questions/1546717
        table = str.maketrans(
            {
                "<": "&lt;",
                ">": "&gt;",
                "&": "&amp;",
                "'": "&apos;",
                '"': "&quot;",
            }
        )

        part["satz"] = part["satz"].translate(table)

        # print(f" satz {part['satz']}")
        for key in sorted(part):  # DEBUG
            print(f":{key}:{part[key]}")
        return part["satz"]

    def _xText(self, *, node, select):
        try:
            r = node.xpath(select, namespaces=NSMAP)[0]
            # print (f"XXXX{r.text}")
            return r.text
        except:
            return None  # python returns implict None, but let's be explicit here

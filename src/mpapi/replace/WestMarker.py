from lxml import etree
from MpApi.Module import Module
from MpApi.Search import Search
from mpapi.constants import NSMAP

"""
    set marker SM8HF in onlineBeschreibung if it doesn't exist yet
"""

marker = "SM8HF"


class WestMarker:
    def Input(self):
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
        # return STOs
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

    def onItem(self):
        return self.checkMarker

    def checkMarker(self, *, itemN, user):
        """
        Check if onlineBeschreibung exists; if not add marker in first description.
        If it exists, check if first description has marker. If not, add it.
        """
        Id = itemN.xpath("@id")[0]

        rGrp = itemN.xpath(
            "m:repeatableGroup[@name='ObjTextOnlineGrp']", namespaces=NSMAP
        )

        if len(rGrp) > 0:
            # if multiple onlineBeschreibungen, we'll write ONLY in first
            # if somebody else changes order, we're screwed
            # so we look at all repeatableGroupItems
            print("   online description exists already")
            valueL = rGrp[0].xpath(
                "m:repeatableGroupItem/m:dataField[@name='TextClb']/m:value",
                namespaces=NSMAP,
            )

            # list comprehension?
            found = 0
            for value in valueL:
                if marker in value.text:
                    found += 1
                    print("\tfound marker, no change necessary")
                    return {}  # no payload

            if found == 0:
                print("   marker not in online description")
                return self.updateOnlineDescription(node=rGrp[0], Id=Id)
        else:
            print("   no online description yet, ADDING MY MARK")
            return self.createOnlineDescription(objId=Id)

    def createOnlineDescription(self, *, objId) -> dict:
        """
        Caution: The id we need here is objId, not the STOid
        """
        rGrpName = "ObjTextOnlineGrp"
        module = "Object"

        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules>
                    <module name="{module}">
                        <moduleItem id="{objId}">
                            <repeatableGroup name="{rGrpName}">
                              <repeatableGroupItem>
                                <dataField name="TextHTMLClb">
                                  <value>&lt;div&gt;[SM8HF]&lt;/div&gt;</value>
                                </dataField>
                                <dataField name="TextClb">
                                  <value>[SM8HF]</value>
                                </dataField>
                                <vocabularyReference name="TypeVoc" id="66645" instanceName="ObjTextOnlineTypeVgr">
                                  <vocabularyReferenceItem id="2899477"/>
                                </vocabularyReference>
                              </repeatableGroupItem>
                            </repeatableGroup>
                        </moduleItem>
                    </module>
                </modules>
            </application>"""
        # print (xml)
        m = Module(xml=xml)
        m.validate()

        payload = {
            "type": "createRepeatableGroup",
            "module": module,
            "id": objId,
            "repeatableGroup": rGrpName,
            "xml": xml,
            "success": f"{module} {objId}: new online description w/ marker",
        }
        return payload

    def updateOnlineDescription(self, *, node, Id):
        """
        The node we get passed here is __only__ a repeatableGroup fragment
        """
        refId = node.xpath("m:repeatableGroupItem/@id", namespaces=NSMAP)[0]

        # todo: we haven't added marker yet
        # we get the complete rGrp now, in order to reconstruct the complete rGrp
        # we have already parsed it once and determined it has doesn't have marker
        # now we need to add the marker to the first repeatableGroupItem

        module = "Object"
        rGrpName = "ObjTextOnlineGrp"
        # creating a new document for upload
        outer = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
            <modules>
                <module name="{module}">
                    <moduleItem id="{Id}">
                    </moduleItem>
                </module>
            </modules>
        </application>
        """
        ET = etree.fromstring(outer)
        # add marker to first rGrp
        htmlN = node.xpath(
            "m:repeatableGroupItem/m:dataField[@name='TextHTMLClb']/m:value",
            namespaces=NSMAP,
        )[0]
        textN = node.xpath(
            "m:repeatableGroupItem/m:dataField[@name='TextClb']/m:value",
            namespaces=NSMAP,
        )[0]
        # print (f"text {htmlN}")
        htmlN.text = htmlN.text + " " + marker
        textN.text = textN.text + " " + marker
        itemN = ET.xpath("//m:moduleItem", namespaces=NSMAP)[0]
        itemN.append(node)

        doc = etree.ElementTree(ET)
        doc.write("debug.xml", pretty_print=True, encoding="UTF-8")
        xml = etree.tostring(
            ET, pretty_print=True, encoding="unicode"
        )  # dont return bytes
        xml = xml.encode()  # force UTF8

        # print(type(xml))
        # print (xml)
        print(f"\tUPDATING ONLINE DESC for {Id}")
        # print (f"refId {refId}")

        m = Module(tree=ET)
        m.validate()

        if refId is not None:
            payload = {
                "type": "updateRepeatableGroup",
                "module": module,
                "id": Id,
                "repeatableGroup": rGrpName,
                "xml": xml,
                "success": f"{module} {Id}: update online description, adding marker",
                "refId": refId,
            }
            return payload

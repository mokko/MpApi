import datetime
from mpapi.search import Search
from lxml import etree  # type: ignore
from mpapi.module import Module
from mpapi.constants import NSMAP


"""
    For the records in one or more groups, set them to SMB-Freigabe = Nein
    if Freigabe is not already "Nein".

    There are at least two possible cases for the situation
    (a) no SMBfreigabe has been set before -> add a new one
    (b) SMBfreigabe exists already and it's not Nein 
        (probably None or Ja) -> change to Nein.

    Leave records with smbFreigabe = Nein alone.

    "Nein" has the voc ID 4491690
"""


class FreigabeNein:
    def addFreigabeNein(self, *, itemN, user: str) -> dict:
        print("   ADD FREIGABE NEIN")
        Id = itemN.xpath("@id")[0]
        today = datetime.date.today()
        mtype = "Object"
        today = datetime.date.today()

        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
              <modules>
                <module name="{mtype}">
                  <moduleItem id="{Id}">
                    <repeatableGroup name="ObjPublicationGrp">
                        <repeatableGroupItem>
                            <dataField dataType="Date" name="ModifiedDateDat">
                                <value>{today}</value>
                            </dataField>
                            <dataField dataType="Varchar" name="ModifiedByTxt">
                                <value>EM_MM1</value>
                            </dataField>
                           <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                             <vocabularyReferenceItem id="4491690"/>
                           </vocabularyReference>
                           <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                             <vocabularyReferenceItem id="2600647"/>
                           </vocabularyReference>
                       </repeatableGroupItem>
                    </repeatableGroup>
                  </moduleItem>
                </module>
              </modules>
            </application>
        """

        payload = {
            "type": "createRepeatableGroup",
            "module": mtype,
            "id": Id,
            "repeatableGroup": "ObjPublicationGrp",
            "xml": xml,
            "success": f"{mtype} {Id}: set object smbfreigabe",
        }

        return payload

    def changeFreigabe(self, *, itemN) -> dict:
        print("  CHANGE FREIGABE TO NEIN")
        mtype = "Object"
        objId = itemN.xpath("@id")[0]
        rGrpName = "ObjPublicationGrp"
        # it's conceivable to have more than one rGrp with SMB-Freigabe so die accordingly
        refIdL = itemN.xpath(
            """
            m:repeatableGroup[@name='ObjPublicationGrp']/
            m:repeatableGroupItem[
                m:vocabularyReference/
                m:vocabularyReferenceItem[@id = '2600647']
            ]/@id""",
            namespaces=NSMAP,
        )  # SMB-Digital

        # we need the id of rGrpItem
        refId = refIdL[0]  # if it dies, we have nothing to change
        # print (f"***{refId}")

        if len(refIdL) > 1:
            raise TypeError(
                f"Error: More SMB-Digital nodes than expected! object {objId}"
            )

        vrItemL = itemN.xpath(
            """
            m:repeatableGroup[@name='ObjPublicationGrp']/
            m:repeatableGroupItem[
                m:vocabularyReference/
                m:vocabularyReferenceItem[@id = '2600647']
            ]/
            m:vocabularyReference[@name='PublicationVoc']/
            m:vocabularyReferenceItem
        """,
            namespaces=NSMAP,
        )
        vrItemL[0].attrib["id"] = "4491690"  # change to nein

        xml = self.completeForUpload(mtype=mtype, moduleItem=itemN)
        today = datetime.date.today()

        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules>
                    <module name="Object">
                        <moduleItem id="{objId}">
                            <repeatableGroup name="ObjPublicationGrp">
                                <repeatableGroupItem id="{refId}">
                                    <dataField dataType="Date" name="ModifiedDateDat">
                                        <value>{today}</value>
                                    </dataField>
                                    <dataField dataType="Varchar" name="ModifiedByTxt">
                                        <value>EM_MM1</value>
                                    </dataField>
                                    <vocabularyReference 
                                        name="PublicationVoc" 
                                        id="62649" 
                                        instanceName="ObjPublicationVgr">
                                        <vocabularyReferenceItem id="4491690"/>
                                    </vocabularyReference>
                                    <vocabularyReference 
                                        name="TypeVoc" 
                                        id="62650" 
                                        instanceName="ObjPublicationTypeVgr">
                                        <vocabularyReferenceItem id="2600647"/>
                                    </vocabularyReference>
                                </repeatableGroupItem>
                            </repeatableGroup>
                        </moduleItem>
                    </module>
                </modules>
            </application>
        """

        print(xml)
        payload = {
            "type": "updateRepeatableGroup",
            "module": mtype,
            "id": objId,
            "repeatableGroup": rGrpName,
            "xml": xml,
            "success": f"{mtype} {objId}: change SMBfreigabe to Nein",
            "refId": refId,
        }
        return payload

    def completeForUpload(self, *, mtype, moduleItem):
        """
        receive a single moduleItem as lxml fragment, wrap it into a complete document and
        turn it into upload form.
        """

        outer = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
            <modules>
                <module name="{mtype}">
                </module>
            </modules>
        </application>
        """
        ET = etree.fromstring(outer)
        moduleN = ET.xpath("//m:module", namespaces=NSMAP)[0]
        moduleN.append(moduleItem)
        m = Module(tree=ET)
        m.clean()
        m.uploadForm()
        m.toFile(path="debug.xml")
        xml = m.toString()
        xml.encode()  # force UTF8
        return xml

    def Input(self):
        groups = {
            "debug": "292396",
        }
        return groups

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def onItem(self):
        return self.setObjectFreigabe  # returns a callback

    def search(self, Id, limit=-1):
        """
        We're trying to find records of objects that .
        - are members in certain groups
        - not Primärverpackung
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=Id,  # using voc id
        )
        # query.addCriterion(
        #    operator="notEqualsField",  # notEqualsTerm
        #    field="ObjPublicationGrp.TypeVoc",
        #    value="2600647",  # use id? Daten freigegeben für SMB-digital
        # )
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
        query.print()
        return query

    def setObjectFreigabe(self, *, itemN, user):
        """
        We're inside an Object's nodeItem.
        """
        rGrpItemL = itemN.xpath(
            """
            m:repeatableGroup[@name='ObjPublicationGrp']/
                m:repeatableGroupItem[
                    m:vocabularyReference[@name = 'TypeVoc']/
                    m:vocabularyReferenceItem[@id = '2600647']
                ]
        """,
            namespaces=NSMAP,
        )  # SMB-Freigabe

        # print (rGrpItemL)

        # it's technically possible to have multiple SMB-Freigaben...
        # although that should not happen
        if len(rGrpItemL) == 1:
            vRefL = rGrpItemL[0].xpath(
                """
                m:vocabularyReference/
                m:vocabularyReferenceItem[@id='1810139']
            """,
                namespaces=NSMAP,
            )  # Ja
            if len(vRefL) > 0:
                # there is a smb-freigabe = yes already, so change it
                # don't do anything if SMB Freigabe != Ja.
                # That may not always be the right thing to do!
                # i could pass rGrpItemL[0] instead
                return self.changeFreigabe(itemN=itemN)
            vRefL = rGrpItemL[0].xpath(
                """
                m:vocabularyReference/
                m:vocabularyReferenceItem[@id='4491690']
            """,
                namespaces=NSMAP,
            )  # Nein
            if len(vRefL) > 0:
                print("   item has already Freigabe = Nein")

            # if there is Freigabe = Nein already, so do nothing
            # To Do: We should also set it to Nein if there is no entry
            # but not sure how to test for that in xpath
            # let's wait until we have test data
        elif len(rGrpItemL) > 1:
            raise SyntaxError("Error: Multiple SMB Freigaben!")
        elif len(rGrpItemL) == 0:
            # there is no smb-freigabe yet, so add one
            return self.addFreigabeNein(itemN=itemN, user=user)
        else:
            raise SyntaxError(f"Unknow Error: {len(rGrpItemL)}")

import datetime
import logging
from Module import Module

class Act: 
    def createOnlineDescription(self, *, objId):
        """
        Caution: The id we might need here is objId, not the STOid
        <dataField dataType="Clob" name="TextHTMLClb">
          <value>&lt;div&gt;[SM8HF]&lt;/div&gt;</value>
        </dataField>
        """

        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules>
                    <module name="Object">
                        <moduleItem id="{objId}">
                            <repeatableGroup name="ObjTextOnlineGrp">
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
        #print (xml)
        m = Module(xml=xml)
        m.validate()
        r = self.api.createRepeatableGroup(
            module="Object", id=objId, repeatableGroup="ObjTextOnlineGrp", xml=xml
        )
        #print (r)
        r.raise_for_status()
        logging.info(f"objId {objId}: new onlineDescription")

    def updateOnlineDescription(self, *, node, id, marker):
        """
            The node we get passed here is only a repeatableGroup fragment
        """
        refId = node.xpath("m:repeatableGroupItem/@id", namespaces=self.NSMAP)[0]

        #todo: we haven't added marker yet
        #we get the complete rGrp now, in order to reconstruct the complete rGrp
        #we have already parsed it once and determined it has doesn't have marker
        #now we need to add the marker to the first repeatableGroupItem

        #creating a new document for upload
        outer = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
            <modules>
                <module name="Object">
                    <moduleItem id="{id}">
                    </moduleItem>
                </module>
            </modules>
        </application>
        """
        ET = etree.fromstring(outer)
        #add marker to first rGrp
        htmlN = node.xpath("m:repeatableGroupItem/m:dataField[@name='TextHTMLClb']/m:value", namespaces=self.NSMAP)[0]
        textN = node.xpath("m:repeatableGroupItem/m:dataField[@name='TextClb']/m:value", namespaces=self.NSMAP)[0]
        #print (f"text {htmlN}")
        htmlN.text = htmlN.text + " " + marker
        textN.text = textN.text + " " + marker
        itemN = ET.xpath("//m:moduleItem", namespaces=self.NSMAP)[0]
        itemN.append(node) 
        
        doc = etree.ElementTree(ET)
        doc.write("debug.xml", pretty_print=True, encoding="UTF-8")  
        xml = etree.tostring(ET, pretty_print=True, encoding="unicode")  # dont return bytes
        xml = xml.encode() # force UTF8

        #print(type(xml))
        #print (xml)
        print (f"\tUPDATING ONLINE DESC for {id}")
        print (f"refId {refId}")

        m = Module(tree=ET)
        m.validate()

        if refId is not None:
            r = self.api.updateRepeatableGroup(
                module="Object", id=id, repeatableGroup="ObjTextOnlineGrp", xml=xml, referenceId=refId
            )
            #print (r)
            r.raise_for_status()
            logging.info(f"objId {objId}: update onlineDescription")


    def setSmbfreigabe(self, *, module="Object", id):
        """
        Sets smbfreigabe to "Ja", but only if smbfreigabe doesn't exist yet. Typically,
        acts on object level.

        Should also determine sensible sort value in case there are freigaben already.
        """
        r = api.getItem(module=module, id=id)
        # test if smbfreigabe already exists; if so, leave it alone
        self._smbfreigabe(module=module, id=id, sort=sort)

    def _smbfreigabe(self, *, module="Object", id, sort=1):
        """
        Sets a freigabe for SMB for a given id. User is taken from credentials.
        Todo:
        - Curently, we setting sort = 1. We will want to test if field is empty in the future or
          rather already has a smbfreigabe. Then we will have to set a better sort value
        """
        today = datetime.date.today()
        xml = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{module}">
              <moduleItem id="{id}">
                <repeatableGroup name="ObjPublicationGrp">
                    <repeatableGroupItem>
                        <dataField dataType="Date" name="ModifiedDateDat">
                            <value>{today}</value>
                        </dataField>
                        <dataField dataType="Varchar" name="ModifiedByTxt">
                            <value>{self.user}</value>
                        </dataField>
                        <dataField dataType="Long" name="SortLnu">
                            <value>{sort}</value>
                        </dataField>
                       <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                         <vocabularyReferenceItem id="1810139"/>
                       </vocabularyReference>
                       <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                         <vocabularyReferenceItem id="2600647"/>
                       </vocabularyReference>
                   </repeatableGroupItem>
                </repeatableGroup>
              </moduleItem>
            </module>
          </modules>
        </application>"""
        m = Module(xml=xml)
        m.validate()
        r = self.api.createRepeatableGroup(
            module=module, id=id, repeatableGroup="ObjPublicationGrp", xml=xml
        )
        r.raise_for_status()
        logging.info(f"objId {objId}: set smbfreigabe")

    def _new_doc (self, *, module, id):
        """
            New doc with a single moduleItem
        """
        xml = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{module}">
              <moduleItem id="{id}"/>
            </module>
          </modules>
        </application>"""

    def _new_repeatableGroup (self, *, name): pass
    """
    add repeatableGroup if group with name doesn't exist yet
    
                <repeatableGroup name="ObjPublicationGrp">
                    <repeatableGroupItem>
                        <dataField dataType="Date" name="ModifiedDateDat">
                            <value>{today}</value>
                        </dataField>
                        <dataField dataType="Varchar" name="ModifiedByTxt">
                            <value>{self.user}</value>
                        </dataField>
                        <dataField dataType="Long" name="SortLnu">
                            <value>{sort}</value>
                        </dataField>
                       <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                         <vocabularyReferenceItem id="1810139"/>
                       </vocabularyReference>
                       <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                         <vocabularyReferenceItem id="2600647"/>
                       </vocabularyReference>
                   </repeatableGroupItem>
                </repeatableGroup>
    """

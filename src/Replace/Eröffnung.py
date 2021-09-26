import datetime
import logging
from lxml import etree
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
        #print (f"refId {refId}")

        m = Module(tree=ET)
        m.validate()

        if refId is not None:
            r = self.api.updateRepeatableGroup(
                module="Object", id=id, repeatableGroup="ObjTextOnlineGrp", xml=xml, referenceId=refId
            )
            #print (r)
            r.raise_for_status()
            logging.info(f"objId {id}: update onlineDescription")


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
        logging.info(f"objId {id}: set smbfreigabe")

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

class Check: 
    def checkDigiP(self, node):
        """
           For a given node, check if multimedia.type="Digitalisat p".
        """
    

    def checkFreigabe(self, *, id, node):
        """
            For a given moduleItem check if SMBFreigabe = Ja,
            
            Should only act if SMBFreigabe does not exist.
            If it is there already, leave it alone.

            TODO:        
            - It would be nice if we could use a callback to determine the action.
            - If id is objId, we could extract that from the moduleItem and dont need to pass it.
            - This is an untested version. I used to include in the following condition in xpath
              but I dont need/want that. However, I didnt test the new version.
              /../../m:vocabularyReference[
                    @name='PublicationVoc']/m:vocabularyReferenceItem[
                    @name='Ja']
        """
        
        try:
            node.xpath(
                """m:repeatableGroup[
                    @name='ObjPublicationGrp']/m:repeatableGroupItem/m:vocabularyReference[
                    @name='TypeVoc']/m:vocabularyReferenceItem[
                    @id='2600647']
                """,
                namespaces=self.NSMAP,
            )[0]
        except IndexError:
            print("   no smbfreigabe yet")
            if self.act is True:
                print (f"\tSETTING smbfreigabe for {id}")
                self._smbfreigabe(id=id, sort=1)
        else:
            print("   smbfreigabe=Ja exists")

    def checkOnlineDescription (self, *, id, node, marker):
        """
            Check if onlineBeschreibung exists; if not add marker in first description.
            If it exists, check if first description has marker. If not, add it.
        """
        rGrp = node.xpath("m:repeatableGroup[@name='ObjTextOnlineGrp']",
            namespaces=self.NSMAP)

        if len(rGrp) > 0:
            #if multiple onlineBeschreibungen, we'll write ONLY in first
            #if somebody else changes order, we're screwed
            #so we look at all repeatableGroupItems
            print("   online description exists already")
            valueL = rGrp[0].xpath("m:repeatableGroupItem/m:dataField[@name='TextClb']/m:value", namespaces=self.NSMAP)
            
            #list comprehension?
            found = 0
            for value in valueL:
                if marker in value.text:    
                    found += 1
                    print ("\tfound marker, no change necessary")

            if found == 0:
                print ("   marker not in online description")
                if self.act is True:
                    self.updateOnlineDescription(node=rGrp[0], id=id, marker=marker)
        else:
            print("   no online description yet, ADDING MY MARK")
            if self.act is True:
                xml = self.createOnlineDescription(objId=id) 
                
    def genericCheck(self, *, field, node, xpath, onNotExist, args):
        """
            Check if xpath expression exists in node. If not call
            onNotExist with args. (generic version of checkFreigabe)
            
            xpath expression is relative to moduleItem.
            
            genericCheck(field="SMBFreigabe", node=n, xpath=x, onNotExist=self._smbfreigabe, args=[id, sort=1])  
        """
        try:
            node.xpath(xpath, namespaces=self.NSMAP)[0]
        except IndexError:
            print(f"   {field} not found")
            if self.act is True:
                print (f"\tWRITING {field}")
                onNotExists(args) #callback
        else:
            print(f"   {field} exists")

from pathlib import Path
from Search import Search
from lxml import etree

"""
    (1) one or multiple searches, saving the results in an etree object.
        For convenience we're also saving the results as file.
    (2) We loop thru the data. We might need multiple loops, e.g. only on Objects or only on Multimedia etc.
    
"""

class Cycle: 
    def genSearch(self, *, limit=-1, searchCB):
        """
            We're trying to write a generic version of perLocId.
        """
        out_fn = f"genCylce.temp.xml" # 

        if self.lazy is True and Path(out_fn).exists():
            print (f"Loading response for temp file {out_fn}")
            ET = self.sar.ETfromFile(path=out_fn) 
        else: 
            print (f"New search")
            rXML = searchCB(limit=limit) # returns XML in some fashion; string for now or ET in future
            self.sar.toFile(xml=rXML, path=out_fn) # temp file for debugging
            ET = etree.fromstring(bytes(rXML, "UTF-8"))

        """ 
            At this point we probably just want to save ET as self.ET and be done with it.
            Let's do the actual loop seperately.
        """
    

    def perLocId (self, *, locId, limit=-1):
        """
        cycles thru the Object records at id, where id identifies a term in genLocationVgr
        which signifies a location.

        This cycle works onlineBeschreibung ([SM8HF]) and SMB-Freigabe.
        Search for a aktueller standort using id from genlocationVgr 
        
        In lazy mode, suppress a new http search request and work with temp file cache.
        Lazy mode can lead to duplicate changes in the db, so CAUTION advised.
        """
        
        out_fn = f"loc{locId}.xml" # 
        needle = "[SM8HF]"
       
        if self.lazy is True and Path(out_fn).exists():
            print (f"Loading response for locId {locId} from file")
            ET = self.sar.ETfromFile(path=out_fn) 
        else: 
            print (f"New search for locId {locId}")
            rXML = self._locSearch(locId=locId, limit=limit)
            self.sar.toFile(xml=rXML, path=out_fn) # temp file for debugging
            ET = etree.fromstring(bytes(rXML, "UTF-8"))
        
        itemsL = ET.xpath(
            "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem",
            namespaces=self.NSMAP,
        )

        for itemN in itemsL:
            objId = itemN.attrib["id"]
            print(objId)
            self.checkOnlineDescription(id=objId,node=itemN, marker=needle)
            self.checkFreigabe(id=objId,node=itemN)

    def _locSearch (self, *, locId, limit=-1):
        """
            make a new search, execute it and return results that list all Object
            records in one location as xml.
        """
        s = Search(module="Object", limit=limit) 
        #experiment with fields
        #s.addField(field="__id")
        #s.addField(field="ObjCurrentLocationVoc")
        #s.addField(field="ObjTextOnlineGrp")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb.ValueTxt")
        s.addCriterion(
            operator="equalsField", 
            field="ObjCurrentLocationVoc",
            value=locId, # using voc id
        )
        #s.print()
        s.validate(mode="search")
        r = self.sar.search (xml=s.toString())
        #r.raise_for_status() # is built into api.search
        #print (r)
        return r.text

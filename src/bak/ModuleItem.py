"""
    Representation of moduleItem; a moduleItem is only a fragment of an xml
    document; it's not a complete xml document.

    <moduleItem hasAttachments="false" id="254808">
      <systemField dataType="Long" name="__id">
        <value>254808</value>
      </systemField>
      ...
    </moduleItem>

    #make new items
    i = moduleItem(hasAttachments="false", id=254808) # new item
#    i = moduleItem(tree=etreeElement)
#    i = moduleItem(xml=XML)
#    i = moduleItem(file="path/to/file.xml")
     
    #deal with fields
    i.systemField (dataType="Long", name="__id", value="254808") # add field
    value = i.systemField (name="__id")                # get value
    
    # SystemField -> usually only getters
    i.__id
    i.__lastmodified
    i.__name
    ...


    #Do we also want to set any of those values? What about those values that are reqeated
    #like uuid? -> we wont figure this out at the moment.

    #vocabularyReference
    <vocabularyReference name="ObjCategoryVoc" id="30349" instanceName="ObjCategoryVgr">
      <vocabularyReferenceItem id="3206642" name="Musikinstrument">
        <formattedValue language="en">Musikinstrument</formattedValue>
      </vocabularyReferenceItem>
    </vocabularyReference>

    #only getters, todo later
    <virtualField name="ObjUuidVrt">
      <value>254808</value>
    </virtualField>

    #Wiederholgruppe
    <repeatableGroup name="ObjObjectNumberGrp" size="1">
      <repeatableGroupItem id="20414895">
        <dataField dataType="Varchar" name="InventarNrSTxt">
          <value>I C 7723</value>
        </dataField>
        ...
    #Reference
    <moduleReference name="InvNumberSchemeRef" targetModule="InventoryNumber" multiplicity="N:1" size="1">
      <moduleReferenceItem moduleItemId="93" uuid="93">
        <formattedValue language="en">EM-S&#252;d- und S&#252;dostasien I C</formattedValue>
      </moduleReferenceItem>
    </moduleReference>

    #Composite?
    <composite name="ObjObjectCre">
      <compositeItem seqNo="0">
        ...
"""
from lxml import etree
from Helper import Helper
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}

class ModuleItem (Helper):
    def __init__(self, *, id=None, hasAttachments="false", tree=None, file=None):
        parser = etree.XMLParser(remove_blank_text=True)
        if id is not None:
            self.etree = etree.Element("{http://www.zetcom.com/ria/ws/module}moduleItem", 
                hasAttachments=hasAttachments, id=id)
            self.systemField(dataType="Long", name="__id", value=id) 
        elif tree is not None:
            self.etree = tree #didnt rm the blanks
        elif xml is not None:
            self.etree = etree.fromstring(xml, parser)
        elif file is not None:
            self.etree = etree.parse(file, parser)

    def attribute(self, *, name, action=None, value=None):
        """
        Remove, add or overwrite attributes in the element moduleItem.
        action: write or remove
        """
        itemL = self.etree.xpath("/m:application/m:modules/m:module/m:moduleItem", 
            namespaces=NSMAP)
        for itemN in itemL:
            if action == "remove":
                itemN.attrib.pop(name, None)
            elif action == "write" and value is not None:
                itemN.attrib[name] = value

    
     

if __name__ == "__main__":
    i = ModuleItem(hasAttachments="false", id="254808")
    i.dataField(name="ObjTechnicalTermClb", value="Zupftrommel")
    self.printToString()
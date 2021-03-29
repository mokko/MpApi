from lxml import etree

"""
    Representation of moduleItem

    <moduleItem hasAttachments="false" id="254808" uuid="254808">
      <systemField dataType="Long" name="__id">
        <value>254808</value>
      </systemField>
      ...
    </moduleItem>

    i = moduleItem (hasAttachments="false", id=254808)
    i.addSystemField (dataType="Long", name="__id", value="254808")
    value = i.getSystemField (name="__id")
    
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
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
dataTypes={
    "Clb": "Clob",
    "Txt": "Varchar"
}

class moduleItem:
    def __init__(self, *, id, hasAttachments="false"):
        self.etree = etree.Element("{http://www.zetcom.com/ria/ws/module}moduleItem", hasAttachments=hasAttachments, id=id)
        self.systemField(dataType="Long", name="__id", value=id) 

    def systemField (self, *, dataType, name, value=None): 
        """
        getter if value is None; else setter.
        
        In most cases you will want to let MuseumPlus create the 
        SystemFields, so i might just as well make this method private"""
         
        if value is None: pass
            #this is a getter, not sure atm how to do tis
        else: #this is a setter
            systemFieldN = etree.SubElement(self.etree, "{http://www.zetcom.com/ria/ws/module}systemField", dataType=dataType, name=name)
            valueN = etree.SubElement(systemFieldN, "{http://www.zetcom.com/ria/ws/module}value") 
            valueN.text = value

    def dataField (self, *, name, dataType=None, value=None):
        """
        <dataField dataType="Clob" name="ObjTechnicalTermClb">
            <value>Zupftrommel</value>
        </dataField>
        """
        if dataType is None:
            typeHint = name[-3:]
            dataType = dataTypes[typeHint]

        if value is None: pass
            #this is a getter, not sure atm how to do tis
        else: #this is a setter
            dataFieldN = etree.SubElement(self.etree, "{http://www.zetcom.com/ria/ws/module}dataField", dataType=dataType, name=name)
            valueN = etree.SubElement(dataFieldN, "{http://www.zetcom.com/ria/ws/module}value") 
            valueN.text = value

    #
    # PUBLIC HELPERS -> check inheritance
    #
               
    def toString(self):
        return etree.tostring(self.etree, pretty_print=True, encoding="unicode")

if __name__ == "__main__":
    i = ModuleItem(hasAttachments="false", id="254808")
    i.dataField(name="ObjTechnicalTermClb", value="Zupftrommel")
    print (i.toString()) 
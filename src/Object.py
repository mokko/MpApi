"""
Object representing module[@name = "Object"]/moduleItem

Should this be called ObjectItem?

What Zetcom calls item I also call a record or Datensatz.

USAGE:

    for item in module():
        print (item)
        
    item = moduleItem(file="path.xml")

    o = Object()                 # make a new Object item from scratch
    o = Object(file="path.xml")  # load from disc
    o = Object(xml=XML_str)      # from xml string
    o = Object(et=lxml.etree)    # from lxml.etree object
    
    #systemField -> usually only getters?
    o.id               or o.__id
    o.lastModified     or o.__lastmodified
    o.name
    ...

    #Do we also want to set any of those values? What about those values that are reqeated
    #like uuid? -> we wont figure this out at the moment.

    #dataField example
    <dataField dataType="Clob" name="ObjTechnicalTermClb">
        <value>Zupftrommel</value>
    </dataField>

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
    # Helpers
    o.toFile()
    o.toString()
"""
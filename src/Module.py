"""
Python object representing moduleItems

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

module is really is a list moduleItems, so we call it moduleList

I guess there could be multiple moduleLists for different kinds of modules
(object, person etc.). At the moment, I assume there is only one.

What Zetcom calls item I also call a record or Datensatz.

USAGE:
    # 4 ways to make a moduleList
    ml = ModuleList(file="path.xml")  # load from disc
    ml = ModuleList(xml=xml)          # from xml string
    ml = ModuleList(etree=lxml.etree) # from lxml.etree object
    ml = ModuleList(name="Object", totalSize=1) # new Object item from scratch

    #new interface
    ml = ModuleList(name="Object", totalSize=1) # new Object item from scratch
    #ml is ModuleList object; 
    #following objects are lxml.etree objects
    mi = ml.moduleItem(hasAttachments="false", id="254808")
    ml.dataField(parent=mi, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    ml.systemField(parent=mi, dataType="Long", name="__id", value="254808")

    rg = ml.repeatableGroup(parent=mi, name=name, size=size)
    rgi = ml.repeatableGroupItem(parent=rg, id=id)
    ml.dataField(parent=rgi, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")

    ml.iter(parent=rg) 
    
    # Helpers
    ml.toFile()
    ml.toString()
    ml.validate()
    
    # internally we store xml in etree object at self.etree
"""
# xpath 1.0 and lxml don't empty string or None for default ns
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}

from lxml import etree
from Helper import Helper


class Module(Helper):
    def __init__(self, *, file=None, tree=None, xml=None, name=None, totalSize=1):
        parser = etree.XMLParser(remove_blank_text=True)
        if tree is not None:
            self.etree = tree  # didnt rm the blanks
        elif xml is not None:
            self.etree = etree.fromstring(xml, parser)
        elif file is not None:
            self.etree = etree.parse(file, parser)
        elif name is not None:
            xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules>
                    <module name="{name}" totalSize="{totalSize}"/>
                </modules>
            </application>"""
            self.etree = etree.fromstring(xml, parser)

    def attribute(self, *, parent=None, name, action=None, value=None):
        """
        Remove, add or overwrite attributes in the element moduleItem.
        action: write or remove
        """
        if parent is None:
            parent = self.etree
        itemL = parent.xpath(
            "/m:application/m:modules/m:module/m:moduleItem", namespaces=NSMAP
        )
        for itemN in itemL:
            if action == "remove":
                itemN.attrib.pop(name, None)
            elif action == "write" and value is not None:
                itemN.attrib[name] = value

    def dataField(self, *, parent, name, dataType=None, value=None):
        """
        <dataField dataType="Clob" name="ObjTechnicalTermClb">
            <value>Zupftrommel</value>
        </dataField>

        If no dataType is given, dataType will be determined based on last
        three characters of name.
        """
        if dataType is None:
            typeHint = name[-3:]
            dataType = dataTypes[typeHint]

        if value is None:
            pass
        # this is a getter, not sure atm how to do tis
        else:  # this is a setter
            dataFieldN = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}dataField",
                dataType=dataType,
                name=name,
            )
            valueN = etree.SubElement(
                dataFieldN, "{http://www.zetcom.com/ria/ws/module}value"
            )
            valueN.text = value

    def moduleItem(self, *, hasAttachments, id):
        """
        <moduleItem hasAttachments="false" id="254808">
            <systemField dataType="Long" name="__id">
                <value>254808</value>
            </systemField>
        </moduleItem>
        """
        mi = etree.Element(
            "{http://www.zetcom.com/ria/ws/module}moduleItem",
            hasAttachments=hasAttachments,
            id=id,
        )

        moduleItemN = self.etree.xpath(
            "/m:application/m:modules/m:module[last()]", namespaces=NSMAP
        )[0]
        moduleItemN.append(mi)
        return mi

    def iter(self, *, parent=None):
        #we could extract the xpath from parent and feed in the next step
        #that would be an consistent interface
        if parent is None:
            axpath = "/m:application/m:modules/m:module/m:moduleItem"
        else:
            axpath = tree.getpath(parent)
            print(axpath)
        itemsN = self.etree.xpath(axpath, namespaces=NSMAP)
        for itemN in itemsN:
            yield itemN

    
    def moduleReference(self, *, parent, name, targetModule, multiplicity, size):
        """
        <moduleReference name="InvNumberSchemeRef" targetModule="InventoryNumber" multiplicity="N:1" size="1">
            <moduleReferenceItem moduleItemId="93" uuid="93">
                <formattedValue language="en">EM-S&#252;d- und S&#252;dostasien I C</formattedValue>
            </moduleReferenceItem>
        </moduleReference>
        """
        return etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}moduleReference",
            name=name,
            multiplicity=multiplicity,
            taretModule=targetModule,
        )

    def repeatableGroup(self, *, parent, name, size):
        """
        <repeatableGroup name="ObjObjectNumberGrp" size="1">
          <repeatableGroupItem id="20414895">
            <dataField dataType="Varchar" name="InventarNrSTxt">
              <value>I C 7723</value>
        """
        return etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}repeatableGroup",
            name=name,
            size=size,
        )

    def repeatableGroupItem(self, *, parent, id):
        return etree.SubElement(
            parent, "{http://www.zetcom.com/ria/ws/module}repeatableGroupItem", id=id
        )

    def systemField(self, *, parent, dataType, name, value=None):
        """
        setter if value is not None; else getter.

        In most cases you will want to let MuseumPlus create the systemFields."""

        if value is None:
            pass
        # this is a getter, not sure atm how to do tis
        else:  # this is a setter
            systemFieldN = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}systemField",
                dataType=dataType,
                name=name,
            )
            valueN = etree.SubElement(
                systemFieldN, "{http://www.zetcom.com/ria/ws/module}value"
            )
            valueN.text = value

    def vocabularyReference(self, *, parent, name, id, instanceName):
        """
        <vocabularyReference name="GeopolVoc" id="61663" instanceName="ObjGeopolVgr">
            <vocabularyReferenceItem id="4399117" name="Land">
                <formattedValue language="en">Land</formattedValue>
            </vocabularyReferenceItem>
        </vocabularyReference>
        """
        return etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}vocabularyReference",
            id=id,
            name=name,
            instanceName=instanceName,
        )

    def vocabularyReferenceItem(self, *, parent, name, id):
        """
        <vocabularyReferenceItem id="4399117" name="Land">
            <formattedValue language="en">Land</formattedValue>
        </vocabularyReferenceItem>
        Todo: getter for formattedValue
        """
        return etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}vocabularyReferenceItem",
            id=id,
            name=name,
        )

    # quick and dirty
    def _rmUuidsInReferenceItems(self, *, parent=None):
        if parent is None:
            parent = self.etree
        itemL = parent.xpath(
            "//m:moduleReference/m:moduleReferenceItem", namespaces=NSMAP
        )
        for eachN in itemL:
            eachN.attrib.pop("uuid", None)

    def _dropFields(self, *, parent=None, type):
        """removes all virtualFields
        Probably virtualFields dont help when changing existing items/records.
        """
        if parent is None:
            parent = self.etree
        typeL = parent.xpath(f"//m:{type}", namespaces=NSMAP)
        for eachN in typeL:
            eachN.getparent().remove(eachN)


if __name__ == "__main__":

    def load_file():
        ml = ModuleList(file="../sdata/exhibitObjects/response.xml")
        print(ml.attribute(name="size"))
        print(ml.attribute(name="totalSize"))  # if no parent, assume self.etree
        for mi in ml.iter(): 
            ml.attribute(parent=mi, name="uuid", action="remove")
            ml._rmUuidsInReferenceItems(parent=mi)
            ml._dropFields(
                parent=mi, type="virtualField"
            )  # if no parent, assume self.etree
            ml._dropFields(
                parent=mi, type="systemField"
            )  # if no parent, assume self.etree
        ml.toFile(path="../sdata/exhibitObjects/response-simplified.xml")
        ml.validate()

    def from_scratch():
        ml = ModuleList(name="Object", totalSize=1)
        mi = ml.moduleItem(hasAttachments="false", id="254808")
        ml.dataField(parent=mi, name="ObjTechnicalTermClb", value="Zupftrommel")
        vr = ml.vocabularyReference(
            parent=mi, name="ObjCategoryVoc", id="30349", instanceName="ObjCategoryVgr"
        )
        ml.vocabularyReferenceItem(parent=vr, id="3206642", name="Musikinstrument")
        rg = ml.repeatableGroup(parent=mi, name="ObjObjectNumberGrp", size="1")
        rgi = ml.repeatableGroupItem(parent=rg, id="20414895")
        ml.dataField(parent=rgi, name="InventarNrSTxt", value="I C 7723")

        for mi in ml.iter(): 
            ml.prints(mi)
        ml.prints()
        ml.validate()
        ml.toFile(path="fromScratch.xml")

    load_file()
    # from_scratch()

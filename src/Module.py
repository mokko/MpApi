"""
Python object representing moduleItems

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

module is really a set of moduleItems.

I guess there could be multiple moduleLists for different kinds of modules
(object, person etc.). At the moment, I assume there is only one.

What Zetcom calls item I also call a record or Datensatz.

USAGE:
    # CONSTRUCTION: 4 ways to make a moduleList
    m = Module(file="path.xml")  # load from disc
    m = Module(xml=xml)          # from xml string
    m = Module(etree=lxml.etree) # from lxml.etree object
    m = Module(name="Object", totalSize=1) # new Object item from scratch

    # WRITING XML FROM SCRATCH
    #m is a Module object; others are lxml.etree objects
    # N is a node, L is a list, T is a etree, E is an element 
    m = Module(name="Object", totalSize=1) # new Object item from scratch

    miN = m.moduleItem(hasAttachments="false", id="254808")
    m.dataField(parent=miN, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    m.systemField(parent=miN, dataType="Long", name="__id", value="254808")

    rgN = m.repeatableGroup(parent=miN, name=name, size=size)
    rgiN = m.repeatableGroupItem(parent=rgN, id=id)
    m.dataField(parent=rgiN, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")

    for eachN in m.iter(parent=rg):
        m.print(eachN)
    
    m.describe()
       
    # HELPERS
    m.toFile()
    m.toString()
    m.validate()

    m._dropRG(parent=miN, name="ObjValuationGrp")
    m._dropFields(parent=miN, type="systemField")
    m._rmUuidsInReferenceItems(parent=miN)    
"""
# xpath 1.0 and lxml don't empty string or None for default ns
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}

from lxml import etree
from Helper import Helper


class Module(Helper):
    def __init__(self, *, file=None, tree=None, xml=None, name=None):
        parser = etree.XMLParser(remove_blank_text=True)
        if tree is not None:
            self.etree = tree  # didnt rm the blanks
        elif xml is not None:
            self.etree = etree.fromstring(xml, parser)
        elif file is not None:
            self.etree = etree.parse(str(file), parser)
        elif name is not None:
            xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules>
                    <module name="{name}"/>
                </modules>
            </application>"""
            self.etree = etree.fromstring(xml, parser)

    def attribute(self, *, parent=None, name, action=None, value=None):
        """
        Remove, add or overwrite attributes in the element moduleItem.
        action: write or remove

        Obsolete! -> let's just use attrib
        for miN in m.iter():
            a = miN.attrib
            if uuid in a:
                print("delete @uuid")
                del a['uuid']
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

    def moduleItem(self, *, hasAttachments=None, id=None):
        """
        <moduleItem hasAttachments="false" id="254808">
            <systemField dataType="Long" name="__id">
                <value>254808</value>
            </systemField>
        </moduleItem>
        """
        mi = etree.Element(
            "{http://www.zetcom.com/ria/ws/module}moduleItem",
        )
        if id is not None:
            mi.set("id", id)
        if hasAttachments is not None:
            mi.set("hasAttachments", hasAttachments)

        moduleItemN = self.etree.xpath(
            "/m:application/m:modules/m:module[last()]", namespaces=NSMAP
        )[0]
        moduleItemN.append(mi)
        return mi

    def iter(self, *, parent=None):
        # we could extract the xpath from parent and feed in the next step
        # that would be an consistent interface
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

    #
    # getter and setter
    #
    def describe(self):
        """
        Reports module types and number of moduleItems per type. Works on self.etree.
        Returns a dictionary like this: {'Object': 173, 'Person': 58, 'Multimedia': 608}
        """
        # report[type] = number_of_items
        known_types = set()
        report = dict()
        moduleL = self.etree.xpath(
            f"/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )
        for moduleN in moduleL:
            moduleA = moduleN.attrib
            known_types.add(moduleA["name"])

        for type in known_types:
            itemL = self.etree.xpath(
                f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem",
                namespaces=NSMAP,
            )
            report[type] = len(itemL)
        return report

    #
    # HELPER
    # quick and dirty
 
    def _dropFields(self, *, parent=None, type):
        """removes all virtualFields
        Probably virtualFields dont help when changing existing items/records.
        """
        if parent is None:
            parent = self.etree
        typeL = parent.xpath(f"//m:{type}", namespaces=NSMAP)
        for eachN in typeL:
            eachN.getparent().remove(eachN)

    def _dropRG(self, *, parent=None, name):
        """
        Drop a repeatableGroup by name. Expects a name, user may provide
        parent node. If no parent provided uses self.etree.
        """
        if parent is None:
            parent = self.etree
        rgL = parent.xpath(f"//m:repeatableGroup[@name ='{name}']", namespaces=NSMAP)
        for rgN in rgL:
            rgN.getparent().remove(rgN)

    def _dropUUID(self):
        """
        Drop all @uuid attributes from the whole document.
        """
        itemL = self.etree.xpath(
            "//m:*[@uuid]", namespaces=NSMAP
        )
        for eachN in itemL:
            eachN.attrib.pop("uuid", None)
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Commandline frontend for Module.py")
    parser.add_argument("-c", "--cmd", help="command", required=True)
    parser.add_argument("-a", "--args", help="arguments", nargs="*")
    args = parser.parse_args()

    m = Module(file=args.args[0])
    print(f"*args: {args}")
    # print (args.cmd)
    # print (args.args)
    result = getattr(m, args.cmd)()
    print(result)

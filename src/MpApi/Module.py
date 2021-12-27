"""
Python object representing moduleItems

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

module is really a set of moduleItems.

What Zetcom calls item I also call a record or Datensatz.

USAGE:
    # CONSTRUCTION: 4 ways to make a moduleList
    m = Module(file="path.xml")  # load from disc
    m = Module(xml=xml)          # from xml string
    m = Module(tree=lxml.etree) # from lxml.etree object
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
# xpath 1.0 and lxml don't allow empty string or None for default ns
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}

from lxml import etree
from MpApi.Helper import Helper


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

        Todo: This method has to go. Currently, it doesn't work like a getter
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
        Create a dataField with name, dataType and value.
        
        If no dataType is given, dataType will be determined based on last
        three characters of name.

        <dataField dataType="Clob" name="ObjTechnicalTermClb">
            <value>Zupftrommel</value>
        </dataField>
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
        Creates a new rGrp and returns it.
        
        Expects
        * parent: lxml node
        * name
        * size

        Returns
        * lxml node

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
        """
        Creates a new rGrpItem and returns it.
        
        Expects
        * parent: lxml node
        * id
        
        Do we really want tocreate an element with an id? Seems like MuseumPlus should
        create that id.
        
        Returns
        * lxml node
        <repeatableGroup name="ObjObjectNumberGrp" size="1">
          <repeatableGroupItem id="20414895">
            <dataField dataType="Varchar" name="InventarNrSTxt">
              <value>I C 7723</value>
        """

        return etree.SubElement(
            parent, "{http://www.zetcom.com/ria/ws/module}repeatableGroupItem", id=id
        )

    def systemField(self, *, parent, dataType, name, value=None):
        """
        Gets a systemField[@name = {name}] if value is None; else sets it with value.

        Expects
        * parent: lxml node
        * dataType: attribute value
        * name: attribute value

        Returns
        * nothing (but changes parent as per side effect)

        New: 
        * Deprecated, should probably go
        * In most cases you will want to let MuseumPlus create the systemFields.

        <systemField dataType="Timestamp" name="__lastModified">
          <value>2021-02-10 11:54:09.993</value>
          <formattedValue language="en">10/02/2021 11:54</formattedValue>
        </systemField>
        """

        if value is None:
            return parent.xpath(f"{http://www.zetcom.com/ria/ws/module}systemField[@name = {name}]")
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

    def totalSize(self, *, module):
        """
        Report the size; only getter. If requested module doesn't exist, return None
        
        Expects
        * module: type, e.g. Object

        Returns
        * integer or None

        EXAMPLE
        <application xmlns="http://www.zetcom.com/ria/ws/module">
           <modules>
              <module name="Object" totalSize="173">
        """
        try:
            return int(self.etree.xpath(
                f"/m:application/m:modules/m:module[@name ='{module}']/@totalSize",
                namespaces=NSMAP,
            )[0])
        except:
            return None # I like eplicit returns

    def vocabularyReference(self, *, parent, name, id, instanceName):
        """
        Makes a new vocabularyReference with name and id and adds it to parent.
        
        Expects:
        * parent: ltree node
        * name: str
        * id: int

        Do we really want to create nodes with ids? Seems that is not what the API wants
        from us.

        EXAMPLE
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
        Makes a new vocabularyReferenceItem with name and id and adds it to parent.

        Expects:
        * parent: ltree node
        * name: str
        * id: int

        Do we really want to create nodes with ids? Seems that is not what the API wants
        from us.

        EXAMPLE
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
        
        Returns 
        * a dictionary like this: {'Object': 173, 'Person': 58, 'Multimedia': 608}
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
    #

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
        itemL = self.etree.xpath("//m:*[@uuid]", namespaces=NSMAP)
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

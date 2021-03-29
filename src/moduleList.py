"""
Python object representing moduleItems

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

module is really is a list moduleItems, so we call it moduleList

What Zetcom calls item I also call a record or Datensatz.

USAGE:
    # 4 ways to make a moduleList
    ml = ModuleList(file="path.xml")  # load from disc
    ml = ModuleList(xml=xml)          # from xml string
    ml = ModuleList(etree=lxml.etree) # from lxml.etree object
    ml = ModuleList(name="Object", totalSize=1) # new Object item from scratch

    #dealing with items
    i = moduleItem(hasAttachments="false", id=254808)
    #i.datafield(dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    ml.item(item=i) # adds item
    ml.item(id=123) # gets item by id  

    for item in moduleList():
        print (item)

    # Helpers
    ml.toFile()
    ml.toString()
    ml.validate()
    
    # internally we store xml in etree object at self.etree
"""
# xpath 1.0 and lxml don't empty string or None for default ns
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
from lxml import etree
from moduleItem import moduleItem

class moduleList:
    def __init__(self, *, file=None, tree=None, xml=None, name=None, totalSize=1):
        parser = etree.XMLParser(remove_blank_text=True)
        if tree is not None:
            self.etree = tree #didnt rm the blanks
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

    def item(self, *, id=None, item=None):
        if id is None and item is None:
            raise TypeError("item needs id or an item object!")
        elif item is not None:
            moduleN = self.etree.xpath("/m:application/m:modules/m:module[last()]", namespaces=NSMAP)[0]
            moduleN.append(item.etree)
    #
    # PUBLIC HELPERS -> check inheritance
    #
               
    def toString(self):
        return etree.tostring(self.etree, pretty_print=True, encoding="unicode")

    def validate(self):
        """
        Validate the search xml expression created.
        """
        if not hasattr(self, "xsd"):
            self.xsd = etree.parse("../data/module_1_4.xsd")
        xmlschema = etree.XMLSchema(self.xsd)
        xmlschema.assertValid(self.etree)
        print("***VALIDATES")

if __name__ == "__main__":
    ml = moduleList(name="Object", totalSize=1)
    i = moduleItem(hasAttachments="false", id="254808")
    ml.item(item=i)
    i.dataField(name="ObjTechnicalTermClb", value="Zupftrommel")
    ml.validate()
    print(ml.toString())
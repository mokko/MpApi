"""
    Represents a single ObjectGroup
    USAGE
        g = ObjectGroup (xml=xml) # should accept string
        g.id
        g.lastModified
        g.name
        for each in g.items():
            print (each) # {id: text}

    Initialize the object loading xml in one of three ways:
    a) from string using xml=string
    b) from file using file=path
    c) or just pass an lxml etree with et=etreeObject
    
    Currently this class doesn't allow to make an ObjectGroup from scratch.
    Is this necessary? This would be necessary to create new records.
"""

from lxml import etree
# xpath 1.0 and lxml don't empty string or None for default ns
NSMAP = {"s": "http://www.zetcom.com/ria/ws/module"}

class ObjectGroup:
    def __init__(self, *, xml=None, file=None, et=None):
        """
        ogr = ObjectGroup(xml="<root/>")
        ogr = ObjectGroup(file="path.xml")
        ogr = ObjectGroup(et=tree)
        """
        parser = etree.XMLParser(remove_blank_text=True)
        if xml is not None:
            self.et = etree.fromstring(xml, parser)
        elif file is not None:
            self.et = etree.parse(file, parser)
        elif et is not None:
            self.et = et #didnt rm the blanks
        #print (etree.tostring(self.et))
        #check no of objectGroups
        size = self.et.xpath("/s:application/s:modules/s:module/@totalSize", namespaces=NSMAP)[0]
        name = self.et.xpath("/s:application/s:modules/s:module/@name", namespaces=NSMAP)[0]
        if int(size) !=1:
            raise TypeError ('Wrong number: ' + size)
        if name != "ObjectGroup":
            raise TypeError ('Wrong type') #todo fix error

        self.id = self.et.xpath("/s:application/s:modules/s:module/s:moduleItem/@id", namespaces=NSMAP)[0]
        self.lastModified = self.et.xpath ("/s:application/s:modules/s:module/s:moduleItem/s:systemField[@name = '__lastModified']/s:value", namespaces=NSMAP)[0]
        self.name =  self.et.xpath (
            "/s:application/s:modules/s:module/s:moduleItem/s:dataField[@name = 'OgrNameTxt']", 
            namespaces=NSMAP)[0]

    def items(self):
        itemsL=self.et.xpath (
            "/s:application/s:modules/s:module/s:moduleItem/s:moduleReference/s:moduleReferenceItem", 
            namespaces=NSMAP)
        for each in itemsL:
            yield (each.get("moduleItemId"), each.xpath("s:formattedValue/text()", namespaces=NSMAP)[0])


    def toString(self): #dryer! inherit
        etree.indent(self.et)
        return etree.tostring(self.et, pretty_print=True, encoding="unicode")  # not UTF-8

if __name__ == "__main__":
   ogr = ObjectGroup(file="..\data\ObjectGroup.xml")
   for each in ogr.items():
       print (each) 
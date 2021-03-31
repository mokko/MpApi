from lxml import etree

class Helper:
    def toString(self, et=None):
        if et is None:
            et = self.etree
        return etree.tostring(et, pretty_print=True, encoding="unicode")

    def prints(self, et=None):
        print(self.toString(et))

    def validate(self, mode="module"):
        """
        Validates a whole xml document of the type module.
        """
        if mode == "module":
            xsdLoc = "../sdata/module_1_4.xsd"
        elif  type == "search":
            xsdLoc = "../sdata/search_1_4.xsd"
        else:
            raise TypeError ("Unknown validation mode")
        #more options for http access?
        
        if not hasattr(self, "xsd"):
            self.xsd = etree.parse(xsdLoc)
        xmlschema = etree.XMLSchema(self.xsd)
        xmlschema.assertValid(self.etree)
        print("***VALIDATES")

    def toFile(self, *, path):
        
        print (type(self.etree))
        doc=self.etree
        #et = etree.ElementTree(self.etree)
        etree.indent(doc)
        doc.write(str(path), pretty_print=True) # appears to write Element

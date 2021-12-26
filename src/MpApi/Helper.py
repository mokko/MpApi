from lxml import etree
from pathlib import Path


class Helper:
    def toFile(self, *, path):
        doc = self.etree
        try:
            self._write(path=path, doc=doc)
        except:
            doc = etree.ElementTree(self.etree)
            self._write(path=path, doc=doc)

    def toFile2(self, *, path):
        doc = self.etree
        doc.write(str(path), pretty_print=True, method="c14n2")

    def _write(self, *, path, doc):
        doc.write(str(path), pretty_print=True, encoding="UTF-8")

    def toString(self, *, et=None):
        if et is None:
            et = self.etree
        return etree.tostring(
            et, pretty_print=True, encoding="unicode"
        )  # why not utf-8?

    def print(self, et=None):
        print(self.toString(et=et))

    def validate(self, *, mode="module"):
        """
        Validates a whole xml document of the type module.

        Typde defaults to "module", "seach" being the other option currently implemented.
        """

        if mode == "module":
            xsdLoc = Path(__file__).joinpath("../../../xsd/module_1_6.xsd").resolve()
        elif mode == "search":
            xsdLoc = Path(__file__).joinpath("../../../xsd/search_1_6.xsd").resolve()
        else:
            raise TypeError("Unknown validation mode")
        # more options for http access?

        if not hasattr(self, "xsd"):
            self.xsd = etree.parse(str(xsdLoc))
        xmlschema = etree.XMLSchema(self.xsd)
        xmlschema.assertValid(self.etree)  # dies if doesn't validate
        return True

    def fromFile(self, *, path):
        self.etree = etree.parse(str(path))

    def fromString(self, *, xml):
        parser = etree.XMLParser(remove_blank_text=True)
        self.etree = etree.fromstring(xml, parser)

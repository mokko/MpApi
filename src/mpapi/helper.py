from lxml import etree
from pathlib import Path
import pkgutil


class Helper:
    def toFile(self, *, path):
        doc = self.etree
        try:
            self._write(path=path, doc=doc)
        except:
            doc = etree.ElementTree(self.etree)
            self._write(path=path, doc=doc)

    def toFile2(self, *, path):  # should not be necessary
        doc = self.etree
        doc.write(str(path), pretty_print=True, method="c14n2")

    def toET(self):
        return self.etree

    def _write(self, *, path, doc):
        # ,pretty_print=True, method="c14n2"
        doc.write(str(path), pretty_print=True, encoding="UTF-8")

    def toString(self, *, et=None):
        if et is None:
            et = self.etree
        return etree.tostring(
            et, pretty_print=True, encoding="unicode"
        )  # why not utf-8?

    # should use __str__ instead -> should go away, deprecated
    def print(self, et=None): 
        print(self.toString(et=et))

    def validate(self, *, mode="module"):
        """
        Validates a whole xml document of the type module.

        Typde defaults to "module", "seach" being the other option currently implemented.
        """

        if mode == "module":
            xsd = pkgutil.get_data(__name__, "data/xsd/module_1_6.xsd")
        elif mode == "search":
            xsd = pkgutil.get_data(__name__, "data/xsd/search_1_6.xsd")
        else:
            raise TypeError("Unknown validation mode")
        # more options for http access?

        # if not hasattr(self, mode):
        self.mode = etree.fromstring(xsd)
        xmlschema = etree.XMLSchema(self.mode)
        xmlschema.assertValid(self.etree)  # dies if doesn't validate
        return True

    def fromFile(self, *, path):
        self.etree = etree.parse(str(path))

    def fromString(self, *, xml):
        parser = etree.XMLParser(remove_blank_text=True)
        self.etree = etree.fromstring(xml, parser)

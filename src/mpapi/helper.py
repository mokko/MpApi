from lxml import etree
from pathlib import Path
import pkgutil
from typing import Union

# from typing import Any
# pathlike = NewType("Pathlike", Union[str, Path])
# ET = NewType("ET", Union [
ET = any

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Helper:
    def fromFile(self, *, path: Path) -> None:
        self.etree = etree.parse(str(path))

    def fromString(self, *, xml: str) -> None:
        parser = etree.XMLParser(remove_blank_text=True)
        self.etree = etree.fromstring(xml, parser)

    def print(self) -> None:
        print(self.toString())

    def toFile(self, *, path: Union[Path, str]) -> None:
        # path can be str or Pathlib object as well
        doc = self.etree
        try:
            self._write(path=str(path), doc=doc)
        except:
            doc = etree.ElementTree(self.etree)
            self._write(path=str(path), doc=doc)

    def toFile2(self, *, path) -> None:  # should not be necessary
        doc = self.etree
        doc.write(str(path), pretty_print=True, method="c14n2")

    def toET(self) -> ET:
        return self.etree

    def toString(self, *, et: ET = None) -> str:
        if et is None:
            et = self.etree
        return etree.tostring(
            et, pretty_print=True, encoding="unicode"
        )  # why not utf-8?

    def validate(self, *, mode: str = "module") -> True:
        """
        Validates a whole xml document of the type module.

        Mode defaults to "module", use "seach" if you're validating a query.
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

    def xpath(self, *, xpath: str):
        return self.etree.xpath(xpath, namespaces=NSMAP)

    def _write(self, *, path, doc) -> None:
        # ,pretty_print=True, method="c14n2"
        doc.write(str(path), pretty_print=True, encoding="UTF-8")

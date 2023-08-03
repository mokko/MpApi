from lxml import etree
from mpapi.constants import NSMAP
from pathlib import Path
import pkgutil
from typing import Union
from zipfile import ZipFile, ZIP_LZMA

# from typing import Any
# pathlike = NewType("Pathlike", Union[str, Path])
# ET = NewType("ET", Union [
ET = any


class Helper:
    def __str__(self):
        return self.toString()

    # def __repr__(self):
    #    return self.toString()

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

    def toZip(self, *, path: Union[Path, str]) -> Path:
        """
        Save module data to a zip file

        Expects path of the unzipped file (as str or path object);
        creates and returns the zipped filepath (with_suffix .zip)

        i.e path is full path ending on .xml

        path: AKu/260k/20221201/query513067-chunk1.xml
        zip_path: AKu/260k/20221201/query513067-chunk1.zip
        short_path: query513067-chunk1.xml
        """
        short_path = Path(path).name
        zip_path = Path(path).with_suffix(".zip")

        with ZipFile(zip_path, "w", compression=ZIP_LZMA) as zip:
            zip.writestr(
                short_path,
                etree.tostring(self.etree, pretty_print=True, encoding="unicode"),
            )
        return zip_path

    def validate(self, *, mode: str = "module") -> True:
        """
        Validates a whole xml document of the type module.

        Mode defaults to "module", use "seach" if you're validating a query.
        """

        if mode == "module":
            xsd = pkgutil.get_data(__name__, "data/xsd/module_1_6.xsd")
        elif mode == "search":
            xsd = pkgutil.get_data(__name__, "data/xsd/search_1_6.xsd")
        elif mode == "voc":
            xsd = pkgutil.get_data(__name__, "data/xsd/vocabulary_1_1.xsd")
        else:
            raise TypeError("Unknown validation mode")
        # more options for http access?

        # if not hasattr(self, mode):
        self.mode = etree.fromstring(xsd)
        xmlschema = etree.XMLSchema(self.mode)
        xmlschema.assertValid(self.etree)  # dies if doesn't validate
        return True

    def xpath(self, xpath: str) -> list:
        """
        Shortcut to access the data in a Module object using lxml's xpath;
        use m: for Zetcom's Module namespace.

        Note: This is the first method with a positional argument that I write
        in a long time.
        """

        return self.etree.xpath(xpath, namespaces=NSMAP)

    def _write(self, *, path, doc) -> None:
        # ,pretty_print=True, method="c14n2"
        doc.write(str(path), pretty_print=True, encoding="UTF-8")

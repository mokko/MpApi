"""
Record represents a single record, e.g. an Object record or a Multimedia record.

Record provides methods to test or change (rewrite) that data.

In the future, there might be different records for the various mtypes

USAGE
    m = Module(file="path.xml")
    r = Record(m) # dies if more than one record
                  # creates a deep copy so that changes to record don't effect original

    # apply to assets
    r.add_reference(targetModule: str, moduleItemId: int) 
                              # add to existing refs
    r.set_creator(ID=1234)    # overwrites existing photographer
    r.set_dateexif(path=path) # overwrites existing exif date
    r.set_filename(path=path) # overwrites existing filename
    r.set_size(path=path)     # overwrites existing size

    #for convenience
    r.toFile("path/to/file.xml")
    m = r.toModule()

    add VS set
    There can be multiple references, but only one filename, so when changing the former 
    we add so to existing references and when changing the latter we overwrite existing
    elements 

FUTURE?
    m = Module(file="path.xml")
    r = record.Multimedia(m)
    r.add_reference(targetModule: str, moduleItemId: int) 
                              # add to existing refs
    r.set_filename(path=path) # overwrites existing filename
    r.set_dateexif(path=path) # overwrites existing exif date
    r.set_size(path=path)     # overwrites existing size

DESIGN CHOICES
- Does Record.py belong to MpApi or to MpApi.Utils? MpApi
- Let's not provide an r.upload() method since this requires credentials
- should we inherit from record and make dedicated record.Multimedia and 
  record.object classes?
- We were considering a crud interface to allow creating, reading, updating, 
  deleting fields. First attempt tried to be too clever and required a 
  database of field types. Next attempt requires this info from user.
"""
import copy
from datetime import datetime
from lxml import etree
from mpapi.module import Module
from pathlib import Path
import pyexiv2

parser = etree.XMLParser(remove_blank_text=True)


class Record:
    def __init__(self, dataM: Module) -> None:
        """
        m = Module(file="path.xml")
        # r contains a copy of m so changes to r are not made to m
        r = Record(m) # dies if more than one record

        """
        if len(dataM) != 1:
            raise TypeError(f"ERROR: Record received {len(dataM)} records!")
        self.module = copy.deepcopy(dataM)  # so we dont change the original

    # should mtype become a property?
    def _mtype(self) -> str:
        return self.module.xpath("/m:application/m:modules/m:module/@name")[0]

    def __str__(self) -> str:
        return self.module.toString()

    #
    # made for multimedia (=asset) records
    #

    def add_reference(self, *, targetModule: str, moduleItemId: int) -> None:
        self.raise_if_not_multimedia()  # would this also work for object records?

        refL = self.module.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/m:composite[@name='MulReferencesCre']"
        )
        if len(refL) == 0:
            lastN = self.module.xpath(
                "/m:application/m:modules/m:module/m:moduleItem/m:*[last()]"
            )[0]
            refN = etree.Element("composite", name="MulReferencesCre")
            lastN.addnext(refN)
        else:
            refN = refL[0]

        xml = f"""<compositeItem seqNo="0">
            <moduleReference name="MulObjectRef" targetModule="{targetModule}" multiplicity="M:N" size="1">
              <moduleReferenceItem moduleItemId="{moduleItemId}" seqNo="0"/>
            </moduleReference>
          </compositeItem>"""
        frag = etree.XML(xml, parser=parser)
        refN.append(frag)

    def raise_if_not_multimedia(self) -> None:
        if self._mtype() != "Multimedia":
            raise TypeError(f"ERROR: Multimedia expected, found {self._mtype()}!")

    def raise_if_not_object(self) -> None:
        if self._mtype() != "Object":
            raise TypeError(f"ERROR: Object expected, found {self._mtype()}!")

    def set_creator(self, *, ID: int) -> None:
        """
        Given the ID for Urheber/Fotograf, we fill out that value.
        What happens if the field already exists? Currently, we're assuming it doesn't.

        From existing record:
        <moduleReference name="MulPhotographerPerRef" targetModule="Person" multiplicity="N:1" size="1">
          <moduleReferenceItem moduleItemId="406600" uuid="406600">
            <formattedValue language="de">Roxane von der Beek</formattedValue>
          </moduleReferenceItem>
        </moduleReference>

        Assumed upload form:
        <moduleReference name="MulPhotographerPerRef" targetModule="Person">
          <moduleReferenceItem moduleItemId="406600"/>
        </moduleReference>
        """
        self.raise_if_not_multimedia()
        ID = int(ID)  # guarantee int-ability

        try:
            modRefN = self.module.xpath(
                """/m:application/m:modules/m:module/m:moduleItem/m:moduleReference[
                @name = 'MulPhotographerPerRef']"""
            )[0]
        except:
            parentN = self.module.xpath(
                """/m:application/m:modules/m:module/m:moduleItem"""
            )[0]
        else:  # if try successfull
            parentN = modRefN.getparent()
            parentN.remove(modRefN)

        xml = f"""<moduleReference name="MulPhotographerPerRef" targetModule="Person">
          <moduleReferenceItem moduleItemId="{ID}"/>
        </moduleReference>"""

        frag = etree.XML(xml, parser=parser)
        parentN.append(frag)

    def set_dateexif(self, *, path: str) -> None:  # alternatively pathlib object
        """
        <dataField dataType="Timestamp" name="MulDateExifTst">
          <value>2011-04-12T16:29:52Z</value>
        </dataField>
        """
        self.raise_if_not_multimedia()
        p = Path(path)
        dateDT = False
        try:
            img = pyexiv2.Image(path)
        except:
            print("WARNING: Can't access exif info")
            # mtime = p.stat().st_mtime
        else:
            try:
                date_str = exif["Exif.Image.DateTime"]  # 2011:04:12 16:29:52
            except:
                print("WARNING Dont find exif date time, using mtime")
                # mtime = p.stat().st_mtime
            else:
                dateDT = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        if not dateDT:
            return
        # dateDT = datetime.utcfromtimestamp(mtime)
        utc = dateDT.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"ddd-new date: {utc}")
        dateExifL = self.module.xpath(
            """
            /m:application/m:modules/m:module/m:moduleItem/m:dataField
                [@name = 'MulDateExifTst']
        """
        )
        if len(dateExifL) > 0:
            dateExifN = dateExifL[0]
            dateExifN.getparent().remove(dateExifN)
            # print("removing original MulDateExifTst")
        # else:
        # print("no MulDateExifTst")
        parentN = self.module.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/m:dataField[last()]"
        )[0]
        xml = f"""<dataField dataType="Timestamp" name="MulDateExifTst">
          <value>{utc}</value>
        </dataField>"""
        frag = etree.XML(xml, parser=parser)
        parentN.addnext(frag)

    def set_filename(self, *, path: str) -> None:
        """
        deletes existing MulOriginalFileTxt, if any, and creates a new one

        pathlib objects are ok for path as well

        - We dont check if the file exists. Only the last part of the path
          (i.e. the filename) is saved, so that path can be a full path.
        - xml has the following shape
          <dataField dataType="Varchar" name="MulOriginalFileTxt">
             <value>VII a 40.jpg</value>
          </dataField>
        """
        self.raise_if_not_multimedia()
        p = Path(path)
        filename = p.name

        origFileL = self.module.xpath(
            """
            /m:application/m:modules/m:module/m:moduleItem/m:dataField
                [@name = 'MulOriginalFileTxt']
        """
        )

        # if it already exists delete it
        if len(origFileL) > 0:
            origFileN = origFileL[0]
            origFileN.getparent().remove(origFileN)
            # print("removing original MulOriginalFileTxt")
        parentN = self.module.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/*[last()]"
        )[0]
        xml = f"""<dataField dataType="Varchar" name="MulOriginalFileTxt">
          <value>{filename}</value>
        </dataField>"""
        frag = etree.XML(xml, parser=parser)
        parentN.addnext(frag)

    def set_size(self, *, path: str) -> None:
        """
        Set the file size in KB.
        If size already exists in RIA, it gets overwritten.

        It seems that RIA always shows values in KB in the form
        <dataField dataType="Varchar" name="MulSizeTxt">
          <value>37 KB</value>
        </dataField>
        The fact that KB is part of the value means that comparing operators
        like "größer als" dont work
        """
        self.raise_if_not_multimedia()
        p = Path(path)
        size = int(p.stat().st_size / 1024)  # from bytes to KB
        # print(f"size {size}")

        mulSizeL = self.module.xpath(
            """
            /m:application/m:modules/m:module/m:moduleItem/m:dataField
                [@name = 'MulSizeTxt']
        """
        )

        if len(mulSizeL) > 0:
            mulSizeN = mulSizeL[0]
            mulSizeN.getparent().remove(mulSizeN)
            # print("removing original MulSizeTxt")

        parentN = self.module.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/*[last()]"
        )[0]
        xml = f"""<dataField dataType="Varchar" name="MulSizeTxt">
          <value>{size} KB</value>
        </dataField>"""
        frag = etree.XML(xml, parser=parser)
        parentN.addnext(frag)

    def toFile(self, path: str) -> None:
        """
        Let's use an unnamed parameter here and see if we'll get used to it.
        """
        self.module.toFile(path=path)

    def toModule(self) -> Module:
        return self.module


if __name__ == "__main__":
    m = Module(file="getItem-Multimedia6549806.xml")
    r = Record(m)
    # print(m)
    # print(r._mtype())
    r.add_reference(targetModule="Object", moduleItemId=1233)
    r.set_filename(path="VII a 40.tif")
    r.set_size(path="VII a 40.tif")
    r.set_dateexif(path="VII a 40.tif")
    r.toFile("test.xml")
    # r.upload()

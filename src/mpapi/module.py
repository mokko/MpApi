"""
Python class representing data in RIA's modules 

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

Theses: 
* a module is really a set of moduleItems.
* What Zetcom calls "item" I also call "record" or a "Datensatz" in other contexts.
* This class should have been called differently, perhaps data or moduleData

Design
* There is an old interface where every method has named parameters (e.g. 
    Module(file="path.xml")
  and there is a new interface which is perhaps more Pythonic
    m3 = m1 + m2

Definition and decisions:
* zml: the xml language we are dealing with here, there are other schemas for search etc.
* a multi-type document is one which has multiple types of moduleItem nodes in 
  different modules (Object, Multimedia). Sometimes I call them types, 
  modules or moduletypes (mtypes).
* Let's usually go with Zetcom's names

USAGE:
    # CONSTRUCTION: 4 ways to make a module
    m = Module(file="path.xml")  # load from disc
    m = Module(xml=xml)          # from xml string
    m = Module(tree=lxml.etree)  # from lxml.etree object
    m = Module()                 # new Object item from scratch CHANGED

    # getting the XML out or validate it 
    m.toFile(path="some.xml")
    xml_str = m.toString()
    lxml = m.toET()  # returns lxml etree document
    m.validate()     # dies if doc doesn't validate

    # inspecting module data     
    adict = m.describe()          # no of items per mtype
    m.totalSize(module="Object")  # no of items as per attribute
    m.actualSize(module="Object") # no of actual items
    sizeInt = len(m)
    itemN = m[("Object",12345)]   # lxml element node that if changed, changes m
    if m:                         # m is True if len(m) > 0 (new)
    nodeL = m.xpath(path="/m:application") # m's shortcut to lxml xpath
    
    #iterate through all moduleItems
    for item in m:
        #do something with item

    for item in m.iter(module="Object"):
        #do something with object item

    # deleting stuff
    m.dropRepeatableGroup(parent=miN, name="ObjValuationGrp")
    m._dropFields(parent=miN, type="systemField")
    m._dropFieldsByName(element="repeatableGroup", name="ObjValuationGrp)
    m._dropAttribs(xpath="m://dataField", name="uuid")
    m.clean()  # drops uuid attributes and certain value elements    

    # other changes to xml
    m.updateTotalSize() # update for all module types
    m.add(doc=ET)
    m3 = m1 + m2

    # WRITING XML FROM SCRATCH
    m = Module()
    objModule = m.module(name="Object")
    item = m.moduleItem(parent=objModule, hasAttachments="false", ID="254808")
    m.dataField(parent=item, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    rgN = m.repeatableGroup(parent=miN, name=name, size=size)
    rgiN = m.repeatableGroupItem(parent=rgN, id=id)
    m.dataField(parent=rgiN, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
"""

from collections import namedtuple  # experimenting with namedtuples
from copy import deepcopy  # for lxml
from lxml import etree  # type: ignore
from mpapi.constants import NSMAP, parser
from mpapi.helper import Helper
from pathlib import Path
from typing import Any, Iterator, Optional, Union

# xpath 1.0 and lxml don't allow empty string or None for default ns
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}
# types
# not using lxml-stubs at the moment
ET = Any
PathX = Union[Path, str]
Item = namedtuple("Item", ["type", "id"])


class Module(Helper):
    def __add__(self, m2):  # pytest complains when I add type hints
        """
        join two Module objects using the + operator:
            m1 = Module(file="one.xml")
            m2 = Module(file="two.xml")
            m3 = m1 + m2

        Note
        * duplicate items are weeded out, i.e. items with identical ids are
          made distinct, only the newest item survives.
        """
        m3 = Module(tree=deepcopy(self.etree))
        m3.add(doc=m2.etree)  # using internal here instead of method from Helper
        return m3

    def __getitem__(self, item: Item) -> ET:
        """
        m = Module(xml=someStr)
        itemN = m[("Object", 1234)]

        EXPECTS
        * a tuple with mtype and ID

        RETURNS
        * lxml.etree._Element object
        """
        mtype = item[0]
        ID = str(item[1])

        itemN: ET = self.xpath(
            f"/m:application/m:modules/m:module[@name = '{mtype}']/m:moduleItem[@id = '{ID}']"
        )[0]
        return itemN

    def __init__(self, *, file: PathX = None, tree: ET = None, xml: str = None) -> None:
        """
        There are FOUR ways to make a new Module object. Pick one:
            m = Module(file="path.xml") # from a file
            m = Module(tree=ET)         # from a lxml etree
            m = Module(xml=xml)         # from string
            m = Module()                # from scratch

        INTERNALS
        * the lxml document is stored in self.etree

        NEW
        * previous versions were not able to deal with multi-type documents;
          now we're in the process of rewriting this module, so that it does
        * to make module from scratch does no longer need a name attribute
        * the method "attribute" used to provide a getter and setter for params
          of moduleItem; this is replaced by new methods like totalSize.
        """

        if tree is not None:
            self.etree = tree
        elif xml is not None:
            # fromstring is for xml without encoding declaration
            if isinstance(xml, bytes):
                self.etree = etree.fromstring(xml, parser)
            else:
                self.etree = etree.fromstring(bytes(xml, "utf-8"), parser)
        elif file is not None:
            self.etree = etree.parse(str(file), parser)
        else:
            # missing <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules/>
            </application>"""
            self.etree = etree.fromstring(xml, parser)

    def __iter__(self) -> ET:
        """
        iterates through all moduleItems, see the method iter if you want to
        iterate more selectively:
            m = Module(xml=xml)
            for moduleItem in m:
                #do something with moduleItem
        """
        apath = "/m:application/m:modules/m:module/m:moduleItem"
        itemsN = self.xpath(apath)
        for itemN in itemsN:
            yield itemN

    def __len__(self):
        """
        Returns the number of all moduleItems, similar to actualSize. Also gets
        used when thruthyness of a module object gets evaluated (where 0 items
        is considered False).
            m = Module()
            if m:
                # doesnt get here

        to check for m's existence:
            try:
                m
        to check type:
            isinstance(m, Module)
        """
        return int(self.xpath("count(/m:application/m:modules/m:module/m:moduleItem)"))

    def __str__(self):
        return self.toString()

    def actualSize(self, *, module: str) -> int:
        """
        Report the actual size of a requested module type (using number of
        moduleItems, not the number of the attribute value. It's getter only.

        If the requested module type or the attribute doesn't exist,
        raises TypeError.

        EXPECTS
        * module: type, e.g. Object

        RETURNS
        * integer

        NEW
        * Used to return None when requested object didn't exist, now raises
          TypeError.

        EXAMPLE
        <application xmlns="http://www.zetcom.com/ria/ws/module">
           <modules>
              <module name="Object" totalSize="173">
        """
        try:
            return int(
                self.xpath(
                    f"count(/m:application/m:modules/m:module[@name ='{module}']/m:moduleItem)"
                )
            )
        except:
            raise TypeError(
                f"Requested module '{module}' doesn't exist or has no moduleItems"
            )

    def add(self, *, doc: ET) -> None:
        """
        add a new doc[ument] to the Module, i.e. join two documents.

        This method doesn't return much, certainly not the result document.
        Instead, it changes self as a side-effect!

        Typically, the new module type doesn't exist yet in the old document.
        Then we add a whole module name="{name}" fragment. But it could also
        be that the module of that type already exists, then we want to keep
        only distinct moduleItems and of non-distinct items only the newer ones.

        Algorithm
        * Loop through the module types of the new document. For every type
        check if that type already exists in the old document and make it if
        necessary.
        * For every moduleItem in newdoc check if it already exists in the old
        and make or replace it if necessary.

        That means we dont need to know what the types in the old doc are.

        m.join(doc=lxml)
        m.join(doc=Module())

        Should doc be an lxml object or another Module?
        NEW
        * At some point, the method add would change doc so that after
          completion, doc was practically empty.
        * The current implmentation is very slow; it takes ca. 20 min to add a
          couple thousand records.
        """
        # List[Union[_Element, Union[_ElementUnicodeResult, _PyElementUnicodeResult, _ElementStringResult]]]
        doc2 = deepcopy(doc)  # leave doc alone, so we don't change it
        d2moduleL = doc2.xpath(  # newdoc
            "/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )

        for d2moduleN in d2moduleL:
            try:
                d2mtypeL: list[ET] = d2moduleN.xpath(
                    "/m:application/m:modules/m:module/@name", namespaces=NSMAP
                )
            except:
                # newdoc has no mtypes, so appears empty, nothing to add
                # print("newdoc appears to be empty")
                return None

            for d2mtype in d2mtypeL:
                # print(f"newdoc mtype: {d2mtype}")
                try:  # Does this mtype exist in old doc?
                    self.xpath(
                        f"/m:application/m:modules/m:module[@name = '{d2mtype}']"
                    )[0]
                except:
                    # old doc doesn't have this mtype, so we add the whole
                    # all of d2's modules[@name = {mtype}]/moduleItems to d1
                    # print (f"d1 doesn't know this mtype {d2mtype}")
                    d1modules = self.xpath("/m:application/m:modules")[0]
                    d1modules.append(d2moduleN)
                else:
                    # new doc's mtype exists already in old doc
                    # we need to compare each item in d1 and d2
                    # print("b4 _compareItems")
                    self._compareItems(mtype=d2mtype, moduleN=d2moduleN)
        self.updateTotalSize()

    def addItem(self, *, itemN: ET, mtype: str):
        """
        Adds a moduleItem to the internal Module object where item is an etree node.

        New:
        - We're now checking if item (with that modItemId) exists already. If so, we're
          discarding the old item before adding the new one.
        - We're working on a deepcopy; otherwise we have xml chaos
        """

        newN = deepcopy(itemN)  # dont touch the original
        modItemId = newN.get("id")
        if self.existsItem(mtype=mtype, modItemId=modItemId):
            self.delItem(mtype=mtype, modItemId=modItemId)

        # it's conceivable that internal module has no module[@name=mtype] yet
        moduleN = self.module(name=mtype)
        moduleN.append(newN)
        self.updateTotalSize()

    def clean(self) -> None:
        """
        New version of the method clean that cleans the present document
        * drops uuid attributes b/c they sometimes don't validate (Zetcom bug)
        * drops Werte und Versicherung to not spill our guts
        * this method doesn't do any validation
        SEE ALSO sanitize
        """
        self.dropUUID()
        self.dropRepeatableGroup(name="ObjValuationGrp")

    def dataField(
        self, *, parent: ET, name: str, dataType: str = None, value: str = None
    ) -> ET:
        """
        Get dataField with that name if it exists or make a new one.

        EXPECTS
        * parent; should be moduleItem
        * name of the dataField
        * dataType (optional): If no dataType is given, dataType will be
          determined based on last three characters of name.
        * value (optional):

        RETURNS
        * dataField as ET

        EXAMPLE
        <dataField dataType="Clob" name="ObjTechnicalTermClb">
            <value>Zupftrommel</value>
        </dataField>
        """
        try:
            dataFieldN = parent.xpath("m:/dataField[@name='{name}']", namespaces=NSMAP)[
                0
            ]
        except:
            if dataType is None:
                typeHint = name[-3:]
                dataType = dataTypes[typeHint]
            if value is None:
                pass
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
        return dataFieldN

    def delItem(self, *, modItemId: int, mtype: str):
        itemN = self.xpath(
            """/m:application/m:modules/m:module[
            @name = '{mtype}'
        ]/m:moduleItem[
            @id = '{str(modItemId)}'
        ]"""
        )[0]

        itemN.getparent().remove(itemN)

    def describe(self) -> dict:
        """
        Reports module types and number of moduleItems per type. Multi-type
        ready.

        RETURNS
        * a dictionary {'Object': 173, 'Person': 58, 'Multimedia': 608}
        """
        # report[type] = number_of_items

        known_types = set()
        report = dict()
        moduleL: list[ET] = self.xpath(f"/m:application/m:modules/m:module")
        for moduleN in moduleL:
            moduleA = moduleN.attrib
            known_types.add(moduleA["name"])

        for Type in known_types:
            itemL: list[ET] = self.xpath(
                f"/m:application/m:modules/m:module[@name = '{Type}']/m:moduleItem"
            )
            report[Type] = len(itemL)
        return report

    def dropUUID(self) -> None:
        """
        Drop all @uuid attributes from the whole document.
        """
        itemL = self.xpath("//m:*[@uuid]")

        for eachN in itemL:
            eachN.attrib.pop("uuid", None)  # Why None here?

    def dropRepeatableGroup(self, *, name):
        """
        Drop a repeatableGroup by name. Expects the rGrp's name.
        """
        rgL = self.xpath(f"//m:repeatableGroup[@name ='{name}']")
        for rgN in rgL:
            rgN.getparent().remove(rgN)

    def existsItem(self, *, mtype: str, modItemId: int):
        try:
            self.__getitem__([(mtype, newId)])
        except:
            return False
        else:
            return True

    def extract_mtypes(self) -> list:
        """
        extracts the mtype; currently meant for cases where Module object has a single record

        What if multiple types exist? Should we return a list?
        """
        return self.xpath("/m:application/m:modules/m:module/@name")

    def extract_mtype(self) -> str:
        """
        Return mtype of single record.

        Raises ValueError if zero or more than 1 mtypes in data
        """

        mtypeL = self.xpath("/m:application/m:modules/m:module/@name")
        if len(mtypeL) == 0:
            raise ValueError("Data has no content")
        if len(mtypeL) > 1:
            raise ValueError("Only one record expected")

        return mtypeL[0]

    def iter(self, *, module: str = "Object") -> Iterator:
        """
        Iterates through moduleItems of the module type provided; use
        __iter__ if you want to iterate over all moduleItems.

        USAGE
        for object in amodule.iter(module="Object")
            #do something w/ object

        EXPECTS
        * module: requested module type to iterate through;

        RETURNS
        * interator

        INTERFACE
        * Do we really need to iterate through a document using this module or
          should we simply use lxml for that?
        """
        apath = f"/m:application/m:modules/m:module[@name ='{module}']/m:moduleItem"
        itemsN = self.xpath(apath)
        for itemN in itemsN:
            yield itemN

    def module(self, *, name: str) -> ET:
        """
        Return module element with that name or make a new one if it
        doesn't exist yet.

        Currently, expects that application/modules exists already which is
        a reasonable assumption given that these elements are created during
        __init__.

        Note: The module element has to have a name and the name is unique.

        Expects
        * name (obligatory): module type; there is no module without a
          name/type.

        Returns
        * module[@name={name}] element as lxml element

        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="Object" totalSize="173">
              <moduleItem hasAttachments="false" id="254808" uuid="254808">
              ...
        """
        try:
            moduleN = self.xpath(f"/m:application/m:modules/m:module[@name='{name}']")[
                0
            ]
        except:
            # modules should always exist, module doesn't
            modulesN = self.xpath("/m:application/m:modules")[0]
            moduleN = etree.SubElement(
                modulesN,
                "{http://www.zetcom.com/ria/ws/module}module",
                name=name,
            )
            # might be append instead: modulesN.append(moduleN)...
        return moduleN

    def moduleItem(
        self, *, parent: ET, ID: int = None, hasAttachments: Optional[str] = None
    ) -> ET:
        """
        Gets moduleItem with that ID or creates a new one.

        EXPECTS
        * parent: parent node (should be module)
        * ID: int
        * hasAttachments (optional): True, False, None

        RETURNS
        * moduleItem as ET

        EXAMPLE
        <moduleItem hasAttachments="false" id="254808">
            <systemField dataType="Long" name="__id">
                <value>254808</value>
            </systemField>
        </moduleItem>
        """
        try:
            item = parent.xpath(
                f"/m:moduleItem[@id = '{ID}'",
                namespaces=NSMAP,
            )[0]
        except:
            item = etree.Element(
                "{http://www.zetcom.com/ria/ws/module}moduleItem",
            )
            if ID is not None:
                item.set("id", str(ID))
            if hasAttachments is not None:
                item.set("hasAttachments", hasAttachments.lower())
            parent.append(item)
        return item

    def moduleReference(
        self,
        *,
        parent: ET,
        name: str,
        targetModule: Optional[str] = None,
        multiplicity: Optional[str] = None,
    ) -> ET:
        """
        Get existing moduleReference with that name or make new one.

        EXPECTS
        * parent: parent node as ET
        * name
        * targetModule

        RETURNS
        * lxml element

        EXAMPLE
        <moduleReference name="InvNumberSchemeRef" targetModule="InventoryNumber" multiplicity="N:1" size="1">
            <moduleReferenceItem moduleItemId="93" uuid="93">
                <formattedValue language="en">EM-S&#252;d- und S&#252;dostasien I C</formattedValue>
            </moduleReferenceItem>
        </moduleReference>
        """
        try:
            modRefN = parent.xpath(
                f"./m:moduleReference[@name = '{name}']",
                namespaces=NSMAP,
            )[0]
        except:
            modRefN = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}moduleReference",
                name=name,
            )
            if targetModule is not None:
                modRefN.set("targetModule", targetModule)

            if multiplicity is not None:
                modRefN.set("multiplicity", multiplicity)
        return modRefN

    def moduleReferenceItem(self, *, parent: ET, moduleItemId: int):
        """
        Make a new moduleReferenceIte.

        NEW
        - no more getter
        """
        mri = etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}moduleReferenceItem",
            moduleItemId=str(moduleItemId),
        )
        return mri

    def repeatableGroup(self, *, parent: ET, name: str, size: int = None):
        """
        Get existing repeatableGroup with that name or creates a new one.

        EXPECTS
        * parent: lxml node
        * name
        * size

        RETURNS
        * lxml node

        EXAMPLE
        <repeatableGroup name="ObjObjectNumberGrp" size="1">
          <repeatableGroupItem id="20414895">
            <dataField dataType="Varchar" name="InventarNrSTxt">
              <value>I C 7723</value>
        """
        try:
            rGrp = parent.xpath(
                f"./m:repeatableGroup[@name = '{name}']",
                namespaces=NSMAP,
            )[0]
        except:
            rGrp = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}repeatableGroup",
                name=name,
            )
            if size is not None:
                rGrp.set("size", size)
        return rGrp

    def repeatableGroupItem(self, *, parent: ET, ID: int = None):
        """
        Make a new rGrpItem

        EXPECTS
        * parent: lxml node
        * ID (optional)

        RETURNS
        * lxml node

        DESIGN
        * Old version used to return a list of nodes
        * No more getter

        <repeatableGroup name="ObjObjectNumberGrp" size="1">
          <repeatableGroupItem id="20414895">
            <dataField dataType="Varchar" name="InventarNrSTxt">
              <value>I C 7723</value>
        """
        itemN = etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}repeatableGroupItem",
        )
        if ID is not None:
            itemN.set("id", str(ID))
        return itemN

    def totalSize(self, *, module: str) -> int:
        """
        Report the totalSize of a requested module (as provided by the xml
        attribute of the same name not by counter moduleItems). It's getter
        only , use updateTotalSize for writing attributes after counting
        moduleItems.

        If the requested module type or the attribute doesn't exist,
        raises TypeError (IndexError?).

        Note that RIA returns the number of "hits" to the query in the
        totalSize attribute. This may differ from the number of actually
        returned items (e.g. if offset or limit) are used. See actualSize.

        EXPECTS
        * module: type, e.g. Object

        RETURNS
        * integer

        NEW
        * Used to return None when requested object didn't exist, now raises
          TypeError.
        * Todo write tests for the errors this method can throw!

        EXAMPLE
        <application xmlns="http://www.zetcom.com/ria/ws/module">
           <modules>
              <module name="Object" totalSize="173">
        """
        try:
            return int(
                self.xpath(
                    f"/m:application/m:modules/m:module[@name ='{module}']/@totalSize"
                )[0]
            )
        except:
            raise TypeError(
                f"Requested module '{module}' or attribute totalSize doesn't exist"
            )

    def updateTotalSize(self) -> None:
        """
        Update or create the totalSize attribute for all module types in the
        document.

        Should work also for moduleItems without a totalSize attribute.

        EXAMPLE
        <application xmlns="http://www.zetcom.com/ria/ws/module">
           <modules>
              <module name="Object" totalSize="173">
        """
        knownTypes = self._types()

        for modType in knownTypes:
            # items per modType
            itemsL = self.xpath(
                f"/m:application/m:modules/m:module[@name = '{modType}']/m:moduleItem"
            )
            try:
                moduleN = self.xpath(
                    f"/m:application/m:modules/m:module[@name = '{modType}']"
                )[0]
            except:
                pass  # it's not an error if file has no items that can be counted
            else:
                # print (f".............updating totalSize for {modType}")
                attributes = moduleN.attrib
                attributes["totalSize"] = str(int(len(itemsL)))

    def _parse_ident_in_parts(self, *, nr):  # xxx
        partsL = [x.strip() for x in nr.split()]
        part1 = partsL[0]
        part2 = " " + partsL[1]
        part3 = " ".join(partsL[2:])

        return [part1, part2, part3]

    def uploadForm(self) -> None:
        """
        Rewrites module in upload form. Expects module in download form.

        Download form is the xml that comes out of RIA, upload form is the form
        RIA expects for uploads.

        We save data in self.etree.

        Transformations
        - drop all virtualFields, systemFields, formattedValue

        QUESTIONS:
        - Returns a copy or rewrites itself? Act as clean, so rewrite itself
        """

        # we want to preserve systemField:__orgUnit
        # self._dropFields(element="systemField")
        self._dropFieldsByName(element="systemField", name="__id")
        self._dropFieldsByName(element="systemField", name="__lastModified")
        self._dropFieldsByName(element="systemField", name="__lastModifiedUser")
        self._dropFieldsByName(element="systemField", name="__createdUser")
        self._dropFieldsByName(element="systemField", name="__created")
        self._dropFieldsByName(element="systemField", name="__uuid")

        self._dropFields(element="virtualField")
        self._dropFields(element="formattedValue")

        # upload sometimes wants id, sometimes not
        # self._dropAttribs(xpath="//m:moduleItem", attrib="id")
        # do we need to eliminate size attributes in repeatableGroups?
        self._dropAttribs(xpath="//m:repeatableGroup", attrib="size")
        self._dropAttribs(xpath="//m:moduleItem", attrib="uuid")

        # various attributes in moduleReference? name we need to keep
        # <moduleReference name="InvNumberSchemeRef" targetModule="InventoryNumber" multiplicity="N:1" size="1">
        # self._dropAttribs(xpath="//m:moduleReference", attrib="targetModule")
        # self._dropAttribs(xpath="//m:moduleReference", attrib="multiplicity")
        # self._dropAttribs(xpath="//m:moduleReference", attrib="size")
        self._dropAttribs(xpath="//m:vocabularyReference", attrib="id")
        self._dropAttribs(xpath="//m:vocabularyReference", attrib="instanceName")
        self._dropAttribs(xpath="//m:vocabularyReferenceItem", attrib="name")
        self._dropAttribs(xpath="//m:module", attrib="totalSize")
        self._dropAttribs(xpath="//m:moduleItem", attrib="hasAttachments")
        self._dropAttribs(xpath="//m:dataField", attrib="dataType")
        # sometimes we want to have the rGrpItem@id
        # self._dropAttribs(xpath="//m:repeatableGroupItem", attrib="id")
        # self._dropAttribs(xpath="//m:moduleReferenceItem", attrib="seqNo")
        # self._dropAttribs(xpath="//m:compositeItem", attrib="seqNo")
        # modifiedBy, modifiedDate
        #    <dataField dataType="Varchar" name="ModifiedByTxt">
        #      <value>EM_EM</value>
        #    </dataField>
        #    <dataField dataType="Date" name="ModifiedDateDat">
        #      <value>2010-05-07</value>
        #    </dataField>
        self._dropFieldsByName(element="dataField", name="ModifiedByTxt")
        self._dropFieldsByName(element="dataField", name="ModifiedDateDat")
        self._dropFieldsByName(element="dataField", name="ObjRecordCreatedByTxt")
        self._dropFieldsByName(element="dataField", name="ObjInventoryDateDat")
        self._dropFieldsByName(element="dataField", name="DatestampFromFuzzySearchLnu")
        self._dropFieldsByName(element="dataField", name="DatestampToFuzzySearchLnu")
        # self._dropFieldsByName(element="moduleReference", name="ObjObjectGroupsRef")
        self._dropFieldsByName(element="moduleReference", name="ObjMultimediaRef")

    def vocabularyReference(
        self, *, parent: ET, name: str, instanceName: str = None, ID: int = None
    ) -> ET:
        """
        Get vocabularyReference with that name if it exists or make a new one.

        EXPECTS
        * parent: ltree node
        * name: str
        * id: int

        RETURNS
        * vocabularyReference as ET

        INTERFACE
        * Do we really want to create nodes with ids? Seems that is not what
          the API wants from us. So make it optional.

        EXAMPLE
        <vocabularyReference name="GeopolVoc" id="61663" instanceName="ObjGeopolVgr">
            <vocabularyReferenceItem id="4399117" name="Land">
                <formattedValue language="en">Land</formattedValue>
            </vocabularyReferenceItem>
        </vocabularyReference>
        """
        try:
            vr = parent.xpath(
                f"m:vocabularyReference[@name = '{name}']", namespaces=NSMAP
            )[0]
        except:
            # print (f"vr with name {name} doesn't exist yet")
            vr = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}vocabularyReference",
                name=name,
            )

            if instanceName is not None:
                vr.set("instanceName", instanceName)

            if ID is not None:
                vr.set("id", str(ID))
        return vr

    def vocabularyReferenceItem(
        self, *, parent: ET, name: str = None, ID: int = None
    ) -> ET:
        """
        Get an existing vocabularyReferenceItem (vri) with that name or make a
        new one and return it.

        EXPECTS
        * parent: ltree node
        * name: str
        * ID (optional): int

        RETURNS
        * vocabularyReferenceItem as ET_element

        INTERFACE
        * Do we really want to create nodes with ids? Seems that is not what
          the API wants from us, so providing an option seems ok.
        * Do we need a getter as well? If we provide it in the future this
          method should not be called
            addVocabularyReferenceItem
        * A getter would be useful to change the vri. So if the vri with that
          name exists already, return it

        EXAMPLE
        <vocabularyReferenceItem id="4399117" name="Land">
            <formattedValue language="en">Land</formattedValue>
        </vocabularyReferenceItem>
        """
        try:
            vri = parent.xpath(
                f"m:vocabularyReferenceItem[@name = '{name}']", namespaces=NSMAP
            )[0]
        except:
            vri = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}vocabularyReferenceItem",
            )
            if name is not None:
                vri.set("name", name)
            if ID is not None:
                vri.set("id", str(ID))
        return vri

    def xpath(self, path: str) -> ET:
        """
        Shortcut to access the data in a Module object using lxml's xpath;
        use m: for Zetcom's Module namespace.

        Note: This is the first method with a positional argument that I write
        in a long time.
        """
        return self.etree.xpath(path, namespaces=NSMAP)

    #
    # HELPER
    #

    def _compareItems(self, *, mtype: str, moduleN: ET):
        # new doc's mtype exists already in old doc
        # now compare each moduleItem in new doc
        newItemsL: list[ET] = moduleN.xpath("./m:moduleItem", namespaces=NSMAP)
        for newItemN in newItemsL:
            newID = int(newItemN.attrib["id"])
            try:
                # item with that ID exists already
                oldItemN = self.xpath(
                    f"/m:application/m:modules/m:module[@name = '{mtype}']/m:moduleItem[@id = '{newID}']"
                )[
                    0
                ]  # IDs should be unique
            except:
                # itemN does not exist in old doc -> copy it over
                d1moduleN = self.xpath(
                    f"/m:application/m:modules/m:module[@name = '{mtype}']"
                )[0]
                d1moduleN.append(newItemN)
            else:
                # itemN exists already, now take the newer one
                oldItemLastModified = self._standardDT(inputN=oldItemN)
                newItemLastModified = self._standardDT(inputN=newItemN)

                if oldItemLastModified < newItemLastModified:
                    # take newItem
                    oldItemN = newItemN  # this will probably not work, but we can debug that later
                    # else: keep oldItem = do nothing

    def _dropAttribs(self, *, attrib, xpath):
        elemL: list[ET] = self.etree.xpath(xpath, namespaces=NSMAP)
        for elemN in elemL:
            try:
                del elemN.attrib[attrib]
            except KeyError:
                pass

    def _dropFields(self, *, element: str, parent: ET = None) -> None:
        """
        removes all elements of the kind {element}.
        Background: Probably virtualFields dont help when changing existing
        items/records, so there might be a need to delete elements.

        DESIGN
        * remains private as I am not sure, if it is useful and remains here

        EXPECTS
        * parent (optional): lxml element; if not specified, acts on Module's
          whole internal document.

        e.g. self._dropFields(element="systemField")
        """

        if parent is None:
            parent = self.etree

        elemL: list[ET] = parent.xpath(f"//m:{element}", namespaces=NSMAP)
        for elemN in elemL:
            elemN.getparent().remove(elemN)

    def _dropFieldsByName(self, *, element: str, name: str) -> None:
        """
        Drop all fields with specified @name.
        """
        # print(f"+++//m:{element}[@name = {name}]")

        elemL: list[ET] = self.etree.xpath(
            f"//m:{element}[@name = '{name}']", namespaces=NSMAP
        )
        for elemN in elemL:
            # print(f"-----------{elemN}")
            elemN.getparent().remove(elemN)

    def _dropIdentNr(self) -> None:
        """
        We want to eliminate identNr as part of sanitizing xml for upload form.
        """

    def _standardDT(self, *, inputN) -> str:
        """
        For a given node containing a dateTime return the date in "standard form"
        as string. The standard form omits special symbols such as TZ and space.
        Also it provides only the first 14 digits, yyyymmddhhmmss b/c they always
        exist, so the resulting number has always the same length. The upshot is
        that the result can be compared in xpath v1 as a number.
        """
        xp = "translate(m:systemField[@name ='__lastModified']/m:value,'-:.TZ ','')"
        new = inputN.xpath(xp, namespaces=NSMAP)
        if len(str(new)) > 13:  # zero-based Python, so 13 is 14
            new = int(str(new)[:13])
        elif len(str(new)) < 13:
            raise TypeError(
                f"The 'since' argument is in an unexpected format ({new} is too short)!"
            )
        # print(f"***{new}")
        return new

    def _types(self) -> set:
        """Returns a set of module types that exist in the document."""
        knownTypes = set()
        moduleL = self.xpath(f"/m:application/m:modules/m:module")

        for moduleN in moduleL:
            moduleA = moduleN.attrib
            knownTypes.add(moduleA["name"])
        return knownTypes

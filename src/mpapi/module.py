"""
Python class representing data in RIA's modules 

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

Thesis: 
* a module is really a set of moduleItems.
* What Zetcom calls "item" I also call "record" or a "Datensatz" in other contexts.
* This class should have been called differently, perhaps data or moduleData

Design
* There is an old interface where every method has named parameters (e.g. 
    Module(file="path.xml")
  and there is a new interface which is perhaps more Pythonic
    m1 + m2

Definition and decisions:
* zml: the xml language we are dealing with here, there are other schemas for search etc.
* a multi-type document is one which has multiple types of moduleItem nodes in 
  different modules (Object, Multimedia). Sometimes I call them types, 
  modules or moduletypes (mtypes).
* Let's usually go with Zetcom's names


USAGE:
    # CONSTRUCTION: 4 ways to make a moduleList
    m = Module(file="path.xml")  # load from disc
    m = Module(xml=xml)          # from xml string
    m = Module(tree=lxml.etree)  # from lxml.etree object
    m = Module()                 # new Object item from scratch CHANGED

    # getting the XML out or validate it 
    m.toFile(path="some.xml")
    xml_str = m.toString()
    lxml = m.toET()  # returns lxml etree document
    m.validate()     # dies if doc doesn't validate
    
    # inspect module data     
    adict = m.describe()          # no of items per mtype
    m.totalSize(module="Object")  # no of items as per attribute
    m.actualSize(module="Object") # no of actual items
    sizeInt = len(m)
    itemN = m[("Object",12345)]   # lxml element node that if changed, changes
                                  # m
    if m:                         # m is True if len(m) > 0 (new)
    
    #iterate through moduleItems
    for item in m:
        #do something with item

    for item in m.iter(module="Object"):
        #do something with object item

    # delete stuff
    m.dropRepeatableGroup(parent=miN, name="ObjValuationGrp")
    m._dropFields(parent=miN, type="systemField")
    m.clean()  # drops uuid attributes and certain value elements    

    # other changes to xml
    m.totalSizeUpdate() # update for all module types
    m.add(doc=ET)
    m3 = m1 + m2

    # WRITING XML FROM SCRATCH
    # Do i really need to write XML from this class? 

    m = Module()
    objModule = m.module(name="Object")
    item = m.moduleItem(parent=objModule, hasAttachments="false", id="254808")
    m.dataField(parent=item, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    rgN = m.repeatableGroup(parent=miN, name=name, size=size)
    rgiN = m.repeatableGroupItem(parent=rgN, id=id)
    m.dataField(parent=rgiN, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
"""

from collections import namedtuple  # experimenting with namedtuples
from copy import deepcopy  # for lxml
from lxml import etree  # type: ignore
from mpapi.helper import Helper
from pathlib import Path
from typing_extensions import TypeAlias  # only in python 3.9?
from typing import Any, Iterator, Optional, Union

# xpath 1.0 and lxml don't allow empty string or None for default ns
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
parser = etree.XMLParser(remove_blank_text=True)
# types
# not using lxml-stubs at the moment
ET = Any

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

    def __getitem__(self, item: Item):
        """
        m = Module(xml=someStr)
        itemN = m[("Object", 1234)]

        EXPECTS
        * a tuple with mtype and ID

        RETURNS
        * lxml.etree._Element object
        """
        mtype = item[0]
        ID = item[1]

        itemN: ET = self.etree.xpath(
            f"/m:application/m:modules/m:module[@name = '{mtype}']/m:moduleItem[@id = '{ID}']",
            namespaces=NSMAP,
        )[0]
        return itemN

    def __init__(self, *, file: Path = None, tree: ET = None, xml: str = None) -> None:
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
            # self.etree = etree.fromstring(xml, parser)
            self.etree = etree.fromstring(bytes(xml, "utf-8"), parser)

        elif file is not None:
            self.etree = etree.parse(str(file), parser)
        else:
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
        apath = f"/m:application/m:modules/m:module/m:moduleItem"
        itemsN = self.etree.xpath(apath, namespaces=NSMAP)
        for itemN in itemsN:
            yield itemN

    def __len__(self):
        """
        Returns the number of all moduleItems, similar to actualSize. Also gets
        used when thruthyness of a module object gets evaluated (where 0 items
        is considered False=.
            m = Module()
            if m:
                # doesnt get here
                # NOTE: before __len__ m would have been True

        to check for m's existance:
            try:
                m
            isinstance(m, Module)
        """
        return int(
            self.etree.xpath(
                f"count(/m:application/m:modules/m:module/m:moduleItem)",
                namespaces=NSMAP,
            )
        )

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
                self.etree.xpath(
                    f"count(/m:application/m:modules/m:module[@name ='{module}']/m:moduleItem)",
                    namespaces=NSMAP,
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
                    self.etree.xpath(
                        f"/m:application/m:modules/m:module[@name = '{d2mtype}']",
                        namespaces=NSMAP,
                    )[0]
                except:
                    # old doc doesn't have this mtype, so we add the whole
                    # all of d2's modules[@name = {mtype}]/moduleItems to d1
                    # print (f"d1 doesn't know this mtype {d2mtype}")
                    d1modules = self.etree.xpath(
                        "/m:application/m:modules", namespaces=NSMAP
                    )[0]
                    d1modules.append(d2moduleN)
                else:
                    # new doc's mtype exists already in old doc
                    # we need to compare each item in d1 and d2
                    # print("b4 _compareItems")
                    self._compareItems(mtype=d2mtype, moduleN=d2moduleN)
        self.totalSizeUpdate()

    def clean(self) -> None:
        """
        New version of the method clean that cleans the present document
        * drops uuid attributes b/c they sometimes don't validate (Zetcom bug)
        * drops Werte und Versicherung to not spill our guts
        * DOES NOT validate.
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
        moduleL: list[ET] = self.etree.xpath(
            f"/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )
        for moduleN in moduleL:
            moduleA = moduleN.attrib
            known_types.add(moduleA["name"])

        for Type in known_types:
            itemL: list[ET] = self.etree.xpath(
                f"/m:application/m:modules/m:module[@name = '{Type}']/m:moduleItem",
                namespaces=NSMAP,
            )
            report[Type] = len(itemL)
        return report

    def dropUUID(self) -> None:
        """
        Drop all @uuid attributes from the whole document.
        """
        itemL = self.etree.xpath("//m:*[@uuid]", namespaces=NSMAP)

        for eachN in itemL:
            eachN.attrib.pop("uuid", None)  # Why None here?

    def dropRepeatableGroup(self, *, name):
        """
        Drop a repeatableGroup by name. Expects the rGrp's name.
        """
        rgL = self.etree.xpath(
            f"//m:repeatableGroup[@name ='{name}']", namespaces=NSMAP
        )
        for rgN in rgL:
            rgN.getparent().remove(rgN)

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
        itemsN = self.etree.xpath(apath, namespaces=NSMAP)
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
            moduleN = self.etree.xpath(
                f"/m:application/m:modules/m:module[@name='{name}']", namespaces=NSMAP
            )[0]
        except:
            modulesN = self.etree.xpath("/m:application/m:modules", namespaces=NSMAP)[
                0
            ]  # should always exist
            moduleN = etree.SubElement(
                modulesN,
                "{http://www.zetcom.com/ria/ws/module}module",
                name=name,
            )
            # might be append instead: modulesN.append(moduleN)...
        return moduleN

    def moduleItem(
        self, *, parent: ET, ID: int, hasAttachments: Optional[str] = None
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
                multiplicity=multiplicity,
                targetModule=targetModule,
            )
        return modRefN

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

    def repeatableGroupItems(self, *, parent: ET):
        """
        Returns existing rGrpItem (only getter).

        EXPECTS
        * parent: lxml node
        * ID (optional)

        RETURNS
        * lxml node LIST

        DESIGN
        * Do we really want to create an element with an id? Seems like
          MuseumPlus should create that ID.

        <repeatableGroup name="ObjObjectNumberGrp" size="1">
          <repeatableGroupItem id="20414895">
            <dataField dataType="Varchar" name="InventarNrSTxt">
              <value>I C 7723</value>
        """
        try:
            itemsL = parent.xpath(
                f"./m:repeatableGroupItem",
                namespaces=NSMAP,
            )
        except:
            itemsL = None
        return itemsL

    def repeatableGroupItemAdd(self, *, parent: ET, ID: Optional[int] = None):

        rGrpItem = etree.SubElement(
            parent,
            "{http://www.zetcom.com/ria/ws/module}repeatableGroupItem",
        )
        if ID is not None:
            rGrpItem.set("id", str(ID))
        return rGrpItem

    def totalSize(self, *, module: str) -> int:
        """
        Report the totalSize of a requested module (as provided by the xml
        attribute of the same name not by counter moduleItems). It's getter
        only , use totalSizeUpdate for writing attributes after counting
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
        * Todo write tests for the erros this method can throw!

        EXAMPLE
        <application xmlns="http://www.zetcom.com/ria/ws/module">
           <modules>
              <module name="Object" totalSize="173">
        """
        try:
            return int(
                self.etree.xpath(
                    f"/m:application/m:modules/m:module[@name ='{module}']/@totalSize",
                    namespaces=NSMAP,
                )[0]
            )
        except:
            raise TypeError(
                f"Requested module '{module}' or attribute totalSize doesn't exist"
            )

    def totalSizeUpdate(self) -> None:
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

        for Type in knownTypes:
            itemsL = self.etree.xpath(
                f"/m:application/m:modules/m:module[@name = '{Type}']/m:moduleItem",
                namespaces=NSMAP,
            )
            try:
                moduleN = self.etree.xpath(
                    f"/m:application/m:modules/m:module[@name = '{Type}']",
                    namespaces=NSMAP,
                )[0]
                attributes = moduleN.attrib
                attributes["totalSize"] = int(len(itemsL))
            except:
                pass  # it is not an error if a file has no items that can be counted

    def vocabularyReference(
        self, *, parent: ET, name: str, instanceName: str, ID: int = None
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
                "m:vocabularyReference[@name = '{name}']", namespaces=NSMAP
            )[0]
        except:
            vr = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}vocabularyReference",
                name=name,
                instanceName=instanceName,
            )
            if ID is not None:
                vr.set("id", str(ID))
        return vr

    def vocabularyReferenceItem(self, *, parent: ET, name: str, ID: int = None) -> ET:
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
                "m:vocabularyReferenceItem[@name = '{name}']", namespaces=NSMAP
            )
        except:
            vri = etree.SubElement(
                parent,
                "{http://www.zetcom.com/ria/ws/module}vocabularyReferenceItem",
                name=name,
            )
            if ID is not None:
                vri.set("id", str(ID))
        return vri

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
                oldItemN = self.etree.xpath(
                    f"/m:application/m:modules/m:module[@name = '{mtype}']/m:moduleItem[@id = '{newID}']",
                    namespaces=NSMAP,
                )[
                    0
                ]  # IDs should be unique
            except:
                # itemN does not exist in old doc -> copy it over
                d1moduleN = self.etree.xpath(
                    f"/m:application/m:modules/m:module[@name = '{mtype}']",
                    namespaces=NSMAP,
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


        """
        if parent is None:
            parent = self.etree

        elemL: list[ET] = parent.xpath(f"//m:{element}", namespaces=NSMAP)
        for elemN in elemL:
            elemN.getparent().remove(elemN)

    def _standardDT(self, *, inputN) -> str:
        """
        For a given node containing a dateTime return the date in standard from
        as string. The standard form omits special symbols such as TZ and
        space. Also it provides only the first 14 digits, yyyymmddhhmmss b/c
        they always exist, so the resulting number has the same length. The
        upshot is that the result can be compared in xpath 1 as a number.
        """
        xp = "translate(m:systemField[@name ='__lastModified']/m:value,'-:.TZ ','')"
        new = inputN.xpath(xp, namespaces=NSMAP)
        if len(str(new)) > 13:  # zero-based Python
            new = int(str(new)[:13])
        elif len(str(new)) < 13:
            raise TypeError(
                f"The 'since' argument is in an unexpected format ({new} is too short)!"
            )
        # print(f"***{new}")
        return new

    def _types(self) -> set:
        """Returns a set of module types in the document."""
        knownTypes = set()
        moduleL = self.etree.xpath(
            f"/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )

        for moduleN in moduleL:
            moduleA = moduleN.attrib
            knownTypes.add(moduleA["name"])
        return knownTypes

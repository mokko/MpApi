"""
Python class representing data in RIA's modules 

<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="173">
      <moduleItem hasAttachments="false" id="254808" uuid="254808">
        ...

Thesis: 
* a module is really a set of moduleItems.
* What Zetcom calls "item" I call a "record" or a "Datensatz".
* This class should be called differently, perhaps data or moduleData

Definition and decisions:
* zml: the xml language we are dealing with here, there are other schemas for search etc.
* a multi-type document is one which has multiple types of moduleItem nodes in 
  different modules (Object, Multimedia). Sometimes I call them types, 
  modules or moduletypes (mtypes).
* Let's go usually go with Zetcom's names

Writing ZML from scratch
This module is in quite a raw state. I wonder in which direction I should take it.
I started to write xml with it, but I haven't used this feature much in the replacer, so
perhaps I dont need it.

* Writing more ZML?
* should I use it to join modules items etc.?
* the attribute method has to go

USAGE:
    # CONSTRUCTION: 4 ways to make a moduleList
    m = Module(file="path.xml")  # load from disc
    m = Module(xml=xml)          # from xml string
    m = Module(tree=lxml.etree)  # from lxml.etree object
    m = Module()                 # new Object item from scratch CHANGED
    
    # delete stuff
    m._dropRG(parent=miN, name="ObjValuationGrp")
    m._dropFields(parent=miN, type="systemField")
    m._rmUuidsInReferenceItems(parent=miN)    

    # inspect stuff     
    m.describe() # mini-statistics
    m.totalSize (module="Object")
    
    #iterate through moduleItems
    for item in m:
        #do something with item

    for item in m.iter(module="Object"):
        #do something with object item

    # change xml
    m.totalSizeUpdate() # update for all module types
    m.add(doc=ET)

    # NEW: Let's write the kind of xml here that the API wants for put requests

    # WRITING XML FROM SCRATCH --> Do i really need to write XML from this class? 
    # Maybe I should just abandon that idea
    mod = Module()
    obj = mod.module(name="Object")
    item = mod.moduleItem(parent=obj, hasAttachments="false", id="254808")
    mod.dataField(parent=item, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")
    rgN = m.repeatableGroup(parent=miN, name=name, size=size)
    rgiN = m.repeatableGroupItem(parent=rgN, id=id)
    m.dataField(parent=rgiN, dataType="Clob", name="ObjTechnicalTermClb", value="Zupfinstrument")

    for eachN in m.iter(parent=rg):
        m.print(eachN)

       
    # HELPERS
    m.toFile()
    m.toString()
    m.validate()
"""

from typing_extensions import TypeAlias  # only in python 3.9?
from typing import Union, Iterator, List, Set
from lxml import etree  # type: ignore
from mpapi.helper import Helper
from copy import deepcopy  # for lxml

# xpath 1.0 and lxml don't allow empty string or None for default ns
dataTypes = {"Clb": "Clob", "Dat": "Date", "Lnu": "Long", "Txt": "Varchar"}
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}
parser = etree.XMLParser(remove_blank_text=True)

# types
ET: TypeAlias = etree._Element
intNone = Union[int, None]
strNone = Union[str, None]


class Module(Helper):
    def __init__(self, *, file: str = None, tree: ET = None, xml: str = None) -> None:
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
            self.etree = etree.fromstring(xml, parser)
        elif file is not None:
            self.etree = etree.parse(str(file), parser)
        else:
            xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
                <modules/>
            </application>"""
            self.etree = etree.fromstring(xml, parser)

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
        moduleL = doc2.xpath(  # newdoc
            "/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )

        for moduleN in moduleL:
            try:
                mtypeL: List[ET] = moduleN.xpath(
                    "/m:application/m:modules/m:module/@name", namespaces=NSMAP
                )
            except:
                # newdoc appears to be empty
                # print("newdoc appears to be empty")
                return None

            for mtype in mtypeL:
                # print(f"newdoc mtype: {mtype}")
                try:
                    # Does this module type exist already in old doc?
                    mod = self.etree.xpath(
                        "/m:application/m:modules/m:module[@name = '{mtype}']"
                    )
                except:
                    # module of mtype doesn't exist yet in old doc, so we add the
                    # whole module fragment, there can be only one
                    modules = self.etree.xpath(
                        "/m:application/m:modules", namespaces=NSMAP
                    )[0]
                    modules.append(moduleN)
                else:
                    # new doc's mtype exists already in old doc
                    # too many indents, so put this in separate method
                    self._compareItems(mtype=mtype, moduleN=moduleN)

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

        Returns
        * a dictionary like this: {'Object': 173, 'Person': 58, 'Multimedia': 608}

        (Internally works on self.etree.)
        """
        # report[type] = number_of_items

        known_types = set()
        report = dict()
        moduleL: List[ET] = self.etree.xpath(
            f"/m:application/m:modules/m:module",
            namespaces=NSMAP,
        )
        for moduleN in moduleL:
            moduleA = moduleN.attrib
            known_types.add(moduleA["name"])

        for Type in known_types:
            itemL: List[ET] = self.etree.xpath(
                f"/m:application/m:modules/m:module[@name = '{Type}']/m:moduleItem",
                namespaces=NSMAP,
            )
            report[Type] = len(itemL)
        return report

    def dropUUID(self, parent=None) -> None:
        """
        Drop all @uuid attributes from the whole document.
        """
        if parent is None:
            parent = self.etree

        itemL = parent.xpath("//m:*[@uuid]", namespaces=NSMAP)

        for eachN in itemL:
            eachN.attrib.pop("uuid", None)  # Why None here?

    def dropRepeatableGroup(self, *, name, parent=None):
        """
        Drop a repeatableGroup by name. Expects a name, user may provide
        parent node. If no parent provided uses self.etree.
        """
        if parent is None:
            parent = self.etree
        rgL = parent.xpath(f"//m:repeatableGroup[@name ='{name}']", namespaces=NSMAP)
        for rgN in rgL:
            rgN.getparent().remove(rgN)

    def iter(self, *, module: str = "Object") -> Iterator:
        """
        Iterates through moduleItems of the module type provided; use
        __iter__ if you want to iterate over all moduleItems.

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

    def moduleItem(self, *, parent: ET, ID: int, hasAttachments: strNone = None) -> ET:
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
        targetModule: strNone = None,
        multiplicity: strNone = None,
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
                taretModule=targetModule,
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

    def repeatableGroupItemAdd(self, *, parent: ET, ID: intNone = None):

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

    def __iter__(self) -> ET:
        """
        m = Module(xml=xml)
        for moduleItem in m:
            #do something with moduleItem
        """
        apath = f"/m:application/m:modules/m:module/m:moduleItem"
        itemsN = self.etree.xpath(apath, namespaces=NSMAP)
        for itemN in itemsN:
            yield itemN

    def _compareItems(self, *, mtype: str, moduleN: ET):
        # new doc's mtype exists already in old doc
        # now compare each moduleItem in new doc
        newItemsL: List[ET] = moduleN.xpath("./m:moduleItem")
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
                moduleN = self.etree.xpath(
                    f"/m:application/m:modules/m:module[@name = '{type}']",
                    namespaces=NSMAP,
                )[0]
                moduleN.append(newItemN)
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

        elemL: List[ET] = parent.xpath(f"//m:{element}", namespaces=NSMAP)
        for elemN in elemL:
            elemN.getparent().remove(elemN)

    def _standardDT(self, *, inputN):
        # since: standard-length is 14 digits now (counting one-based)
        # TODO: not properly tested or debugged
        xpath = "translate(m:/systemField[@name ='__lastModified']/m:value,'-:.TZ ','')"
        new = inputN.xpath(xpath, namespaces=NSMAP)
        if len(str(new)) > 13: # zero-based Python
            new = int(str(new)[:13]) 
        elif len(str(new)) < 13:
            raise TypeError (f"The 'since' argument is in an expected format ({new} is too short)!") 
        return new

    def _types(self) -> Set:
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

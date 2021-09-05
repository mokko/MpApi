"""
Sar stands for "search and response". It's a higher level interface on top of MpApi that 
bundles multiple requests in one method, typically a search and a response. 

I introduce it mainly to clean up the code of the Mink class, so that Mink has to deal less 
with xml and Sar.py can be tested easier. (Conversely, that means that mink parses DSL 
config file, writes files, logs report.) 

Sar typically returns a requests reponse (r) which contains xml in r.text or binary in
r.content. 

Do we expose etree stuff to the user at all? Perhaps not. Let's just use xml strings
everywhere, even if that has a performance penality. 

A set is an xml containing a set of items, typically moduleItems.

USAGE:
    import Sar from Sar
    import Search from Search
    #import Module from Module
    sr = Sar(baseURL=baseURL, user=user, pw=pw)

    #get stuff from single ids; returns request object
    r = sr.getItem(module="Objekt", id="1234")    # returns single item for any module
    r = sr.getActorSet(type="exhibit", id="1234") # Actor items for objects in given exhibit/group
    r = sr.getMediaSet(type="exhibit", id="1234") # Media items for objects in given exhibit/group
    r = sr.getObjectSet(type="group", id="1234")  # Object items in given exhibit/group
    r = sr.getRegistrySet(type="exhibit", id="1234") # Registrar items 

    #search
    s = Search()
    r = sr.search (xml=s.toString())

    #general purpose
    clean_xml = sr.clean(inX=xml) # clean up xml so it validates and has less sensitive info
    xml = sr.definition(module="Objects")
    new_xml = sr.join([xml1, xml2])
    sr.visibleActiveUsers() # returns list of all users visible to user curently logged in
    
    #attachments
    sr.saveAttachments(xml=xml, adir=dir) # for moduleItems in xml download attachments and 
        # save to as adir/{mulId}.{ext}, only d/l media with smbfreigabe.
        # policy="mulId.ext"
        # policy="oldname"

    #modify data
    sr.setSmbfreigabe (module="Object", id="1234") # sets smbfreigabe if doesn't exist yet.
    
    #helpers                   
    xml = sr.xmlFromFile (path=path)
    sr.toFile(xml=xml, path=path)
    xml = sr.EToString (tree=tree)
    ET = sr.ETfromFile (path=path)
"""

import datetime
import os  # b/c Pathlib has troubles with windows network paths
from Search import Search
from MpApi import MpApi
from lxml import etree
from pathlib import Path
from Module import Module

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)


class Sar:  # methods in alphabetical order
    def __init__(self, *, baseURL, user, pw):
        """
        Earlier version stored last search in searchRequest. Eliminated b/c too
        bothersome and I didn't need it.
        """
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.user = user

    def clean(self, *, inX):
        """
        Drop uuid fields b/c they sometimes don't validate (Zetcom bug)
        Drop Werte und Versicherung to not spill our guts
        Also validates.

        Expects xml as string and returns xml as string.
        """
        m = Module(xml=inX)
        m._dropUUID()
        m._dropRG(name="ObjValuationGrp")
        m.validate()
        return m.toString()

    def definition(self, *, module=None):
        """
        Gets definition from server and returns it as xml string.
        """
        return self.api.getDefinition(module=module).text

    def getItem(self, *, module, id):
        """
        Get a single item of specified module by id. Returns a request object.
        """
        return self.api.getItem(module=module, id=id)

    def getActorSet(self, *, type, id):
        """
        Get a set of actors from an exhibit or group.
        Type is either "exhibit" or "group".
        """
        s = Search(module="Person")
        if type == "exhibit":
            s.addCriterion(
                field="PerObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
                operator="equalsField",
                value=id,
            )
        elif type == "group":
            s.addCriterion(
                field="PerObjectRef.ObjObjectGroupsRef.__id",
                operator="equalsField",
                value=id,
            )
        else:
            raise ValueError("Unknown type! {type}")
        return self.api.search(xml=s.toString())

    def getMediaSet(self, *, id, type):
        """
        Get a set multimedia items for exhibits or groups containing objects; returns a
        requests object with a set of items. Returns request object.
        """
        s = Search(module="Multimedia")
        if type == "exhibit":
            s.addCriterion(
                field="MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
                operator="equalsField",
                value=id,
            )
        elif type == "group":
            s.addCriterion(
                field="MulObjectRef.ObjObjectGroupsRef.__id",
                operator="equalsField",
                value=id,
            )
        else:
            raise ValueError("Unknown type! {type}")
        return self.api.search(xml=s.toString())

    def getObjectSet(self, *, id, type):
        """
        Get object items for exhibits or groups; expects id and type. Type is either
        "exhibit" or "group". Returns the request.
        """

        s = Search(module="Object")
        if type == "exhibit":
            s.addCriterion(
                field="ObjRegistrarRef.RegExhibitionRef.__id",
                operator="equalsField",
                value=id,
            )
        elif type == "group":
            s.addCriterion(
                field="ObjObjectGroupsRef.__id", operator="equalsField", value=id
            )
        else:
            raise ValueError("Unknown type! {type}")
        s.validate(mode="search")
        return self.api.search(xml=s.toString())

    def getRegistrySet(self, *, id):
        s = Search(module="Registrar")
        s.addCriterion(
            field="RegExhibitionRef.__id",
            operator="equalsField",
            value=id,
        )
        s.validate(mode="search")
        return self.api.search(xml=s.toString())

    def join(self, *, inL):
        """
        Expects several documents as xml string to join them to one bigger
        document. Returns xml string.
        """
        # print (inL)
        known_types = set()
        firstET = None
        for xml in inL:
            tree = etree.fromstring(bytes(xml, "UTF-8"))
            moduleL = tree.xpath(
                f"/m:application/m:modules/m:module",
                namespaces=NSMAP,
            )
            for moduleN in moduleL:
                moduleA = moduleN.attrib
                known_types.add(moduleA["name"])

            if firstET is None:
                firstET = tree
            else:
                for type in known_types:
                    newItemsL = tree.xpath(
                        f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem",
                        namespaces=NSMAP,
                    )
                    if len(newItemsL) > 0:
                        # only append if there is something to append
                        # print(f"type: {type}")
                        try:
                            lastModuleN = firstET.xpath(
                                f"/m:application/m:modules/m:module[@name = '{type}']",
                                namespaces=NSMAP,
                            )[-1]
                        except:
                            # make a node with the write type
                            modulesN = firstET.xpath(
                                f"/m:application/m:modules", namespaces=NSMAP
                            )[-1]
                            lastModuleN = etree.SubElement(
                                modulesN,
                                "{http://www.zetcom.com/ria/ws/module}module",
                                name=type,
                            )
                        # print(f"len:{len(lastModuleN)} {lastModuleN}")
                        for newItemN in newItemsL:
                            lastModuleN.append(newItemN)
                    # else:
                    #    print ("None found!")

        for type in known_types:  # update totalSize for every type
            itemsL = firstET.xpath(
                f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem",
                namespaces=NSMAP,
            )
            try:
                moduleN = firstET.xpath(
                    f"/m:application/m:modules/m:module[@name = '{type}']",
                    namespaces=NSMAP,
                )[0]
                attributes = moduleN.attrib
                attributes["totalSize"] = str(len(itemsL))
            except:
                pass  # it is not an error if a file is has no items that can be counted

        # print(known_types)
        xml = etree.tostring(firstET, pretty_print=True, encoding="unicode")
        if not xml:
            raise TypeError("Join failed")
        return xml

    def saveAttachments(self, *, xml, adir):
        """
        For a set of multimedia moduleItems, download their attachments.

        Typcially will process moduleItems of type multimeida (aka media). But
        could theoretically also work on different types.

        Expects a xml string and a directory to save the attachments to.
        Attachments are saved to disk with the filename {mulId}.{ext}.

        New: Now uses streaming to save memory.
        New: Download only attachments with Freigabe[Typ = "SMB-Freigabe"] = "Ja"
        """
        E = etree.fromstring(bytes(xml, "UTF-8"))

        itemsL = E.xpath(
            """
            /m:application/m:modules/m:module[@name='Multimedia']
            /m:moduleItem[@hasAttachments = 'true']
            /m:repeatableGroup[@name = 'MulApprovalGrp']
            /m:repeatableGroupItem
            /m:vocabularyReference[@name = 'TypeVoc']
            /m:vocabularyReferenceItem[@name = 'SMB-digital'] 
            /../../..
            /m:repeatableGroupItem
            /m:vocabularyReference[@name = 'ApprovalVoc']
            /m:vocabularyReferenceItem[@name = 'Ja'] 
            /../../../..            
            """,
            namespaces=NSMAP,
        )
        print(
            f" xml has {len(itemsL)} records with attachment=True and Freigabe[@typ='SMB-Digital'] = Ja"
        )

        positives = set()

        for itemN in itemsL:
            itemA = itemN.attrib  # A for attribute
            mmId = itemA["id"]

            # Why do i get suffix from old filename? Is that really the best source?
            # Seems that it is. I see no other field in RIA
            fn_old = itemN.xpath(
                "m:dataField[@name = 'MulOriginalFileTxt']/m:value/text()",
                namespaces=NSMAP,
            )[
                0
            ]  # assuming that there can be only one
            fn = mmId + Path(fn_old).suffix
            mmPath = Path(adir).joinpath(fn)  # need resolve here!
            # print(f"POSITIVE {mmPath}")
            positives.add(mmPath)
            if (
                not mmPath.exists()
            ):  # only d/l if doesn't exist yet, not sure if we want that
                print(f" getting {mmPath}")
                self.api.saveAttachment(module="Multimedia", id=mmId, path=mmPath)
        return positives

    def search(self, *, xml):
        """
        Send a request to the api and return the response. Expects a search in xml
        (Same as in MpApi).
        """
        return self.api.search(xml=xml)

    def setSmbfreigabe(self, *, module="Object", id):
        """
        Sets smbfreigabe to "Ja", but only if smbfreigabe doesn't exist yet. Typically,
        acts on object level.

        Should also determine sensible sort value in case there are freigaben already.
        """
        r = api.getItem(module=module, id=id)
        # test if smbfreigabe already exists; if so, leave it alone
        self._smbfreigabe(module=module, id=id, sort=sort)

    def _smbfreigabe(self, *, module="Object", id, sort=1):
        """
        Sets a freigabe for SMB for a given id. User is taken from credentials.
        Todo:
        - Curently, we setting sort = 1. We will want to test if field is empty in the future or
          rather already has a smbfreigabe. Then we will have to set a better sort value
        """
        today = datetime.date.today()
        xml = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{module}">
              <moduleItem id="{id}">
                <repeatableGroup name="ObjPublicationGrp">
                    <repeatableGroupItem>
                        <dataField dataType="Date" name="ModifiedDateDat">
                            <value>{today}</value>
                        </dataField>
                        <dataField dataType="Varchar" name="ModifiedByTxt">
                            <value>{self.user}</value>
                        </dataField>
                        <dataField dataType="Long" name="SortLnu">
                            <value>{sort}</value>
                        </dataField>
                       <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                         <vocabularyReferenceItem id="1810139"/>
                       </vocabularyReference>
                       <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                         <vocabularyReferenceItem id="2600647"/>
                       </vocabularyReference>
                   </repeatableGroupItem>
                </repeatableGroup>
              </moduleItem>
            </module>
          </modules>
        </application>"""
        m = Module(xml=xml)
        m.validate()
        r = self.api.createRepeatableGroup(
            module=module, id=id, repeatableGroup="ObjPublicationGrp", xml=xml
        )

    # Helper
    def xmlFromFile(self, *, path):
        with open(path, "r", encoding="UTF-8") as f:
            xml = f.read()
        return xml

    def toFile(self, *, xml, path):
        E = etree.fromstring(bytes(xml, "UTF-8"))
        tree = etree.ElementTree(E)
        tree.write(
            str(path), pretty_print=True, encoding="UTF-8"
        )  # appears to write Element

    def EToString(self, *, tree):
        etree.tostring(
            tree, pretty_print=True, encoding="unicode"
        )  # so as not to return bytes

    def ETfromFile(self, *, path):
        return etree.parse(str(path), ETparser)


if __name__ == "__main__":
    import argparse

    # __file__
    with open("../sdata/credentials.py") as f:
        exec(f.read())

    """
    USAGE
        Sar.py -c describe arg1 arg2
    """

    parser = argparse.ArgumentParser(description="Commandline frontend for Sar.py")
    parser.add_argument("-c", "--cmd", help="command", required=True)
    parser.add_argument("-a", "--args", help="arguments", nargs="*")
    args = parser.parse_args()

    s = Sar(baseURL=baseURL, pw=pw, user=user)
    userList = s.visibleActiveUsers()
    print(userList)

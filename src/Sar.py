"""
Sar stands for "search and response". It's a higher level interface on top of MpApi that 
bundles multiple requests together, typically searches and responses. 

I introduce it mainly to clean up the code of the Mink class, so that Mink has to deal less 
with xml and Sar.py can be tested easier. (Conversely, that means that mink parses DSL config 
file, writes files, reports to log and user. 

Sar typically returns a requests reponse (r) which contains xml in r.text or binary in
r.content. 

Do we expose etree stuff to the user at all? Perhaps not. Let's just use xml strings
everywhere, even if that has a performance penality. 

A set is an xml containing a set of items.

USAGE:
    import Sar from Sar
    import Module from Module
    import Search from Search
    sr = Sar(baseURL=baseURL, user=user, pw=pw)

    #get stuff from single ids
    r = sr.getItem(module="Objekt", id="1234")    # returns single item for any module
    r = sr.getActorSet(type="exhibit", id="1234") # Actor items for objects in given exhibit or group
    r = sr.getMediaSet(type="exhibit", id="1234") # Media items for objects in given exhibit or group
    r = sr.getObjectSet(type="group", id="1234")  # Object items in given exhibit or group

    #find out about the last search
    s = sr.searchRequest  # returns the last search request as xml, if any

    #request results for a search request
    s = Search()
    r = sr.search (xml=s.toString())

    #do something with sets
    for content in attachmentsIter(set=xml):
        # do something with content 
    
    #to do stuff with the moduleItems use Module
    m = Module(xml=r.text)
    
    #Helpers                   # quite different sort of stuff, could go to soemewhere else?
    joinZml(globber, out_fn)   # writes result to file
    xml = cleanZml (xml)       # clean up xml so it validates and contains less sensitive info

    sr.toFile(xml, path)
    

Sar : higher level operations with xml
MpApi : basic API operations 
Search | Module : make XML


"""
from Search import Search
from MpApi import MpApi
from lxml import etree
from pathlib import Path
from Module import Module

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Sar:  # methods in alphabetical order
    def __init__(self, *, baseURL, user, pw):
        self.searchRequest = None  # attrib for search requests
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)

    def clean(self, *, inX):
        m = Module(xml=inX)
        c = 0
        for miN in m.iter():
            a = miN.attrib
            c += 1
            #print(f"sar.clean: {c}: id {a['id']} {a}")
            if "uuid" in a:
                del a["uuid"]
        m._rmUuidsInReferenceItems # takes too long
        m._dropRG(name="ObjValuationGrp") # takes too long
        m.validate()
        return m.toString()

    def getItem(self, *, module, id):
        """
        Get a single item of any module by id. Returns a request object.
        Doesn't set self.searchRequest.
        """
        self.searchRequest = None
        return self.api.getItem(module="Multimedia", id=id)

    def getActorSet(self, *, type, id):
        """
        Get actors
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
        self.searchRequest = s.toString()
        return self.api.search(xml=s.toString())

    def getMediaSet(self, *, id, type):
        """
        Get a set multimedia items for exhibits or groups containing objects; returns a
        requests object with a set of items.
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
        self.searchRequest = s.toString()
        return self.api.search(xml=s.toString())

    def getObjectSet(self, *, id, type):
        """
        Get object items for exhibits or groups; expects id and type. Type is either
        "exhibit" or "group". Returns the request. Also sets searchRequest.
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
        self.searchRequest = s.toString()
        return self.api.search(xml=s.toString())

    def join(self, *, inL):
        """
        Expects several documents as lxml.etree objects to join them to one
        bigger document. Returns docN.
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
            moduleN = firstET.xpath(
                f"/m:application/m:modules/m:module[@name = '{type}']", namespaces=NSMAP
            )[0]
            attributes = moduleN.attrib
            attributes["totalSize"] = str(len(itemsL))
        # print(known_types)
        xml = etree.tostring(firstET, pretty_print=True, encoding="unicode")
        if not xml:
            raise TypeError("Join failed")
        return xml

    def saveAttachments(self, *, xml, adir):
        """
        For a set of multimedia moduleItems, download their attachments.

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
        print(f"xml has {len(itemsL)} records with attachment=True and Freigabe[@typ='SMB-Digital'] = Ja")
        
        positives = set()
        
        for itemN in itemsL:
            itemA = itemN.attrib # A for attribute
            mmId = itemA["id"]

            #Why do i get suffix from old filename? Is that really the best source?
            #Seems that it is. I see no other field in RIA
            fn_old = itemN.xpath(
                "m:dataField[@name = 'MulOriginalFileTxt']/m:value/text()",
                namespaces=NSMAP,
            )[0]  # assuming that there can be only one
            fn = mmId + Path(fn_old).suffix
            mmPath = Path(adir).joinpath(fn)
            positives.add(mmPath)
            #print (f"attachment for Multimedia/{mmId}")
            if not mmPath.exists(): # only d/l if doesn't exist yet, not sure if we want that
                print (f" getting {mmPath}")
                self.api.saveAttachment(module="Multimedia", id=mmId, path=mmPath)
        return positves

    def search(self, *, xml):
        """
        Send a request to the api and return the response. Expects a search in xml
        (Same as in MpApi).
        """
        self.searchRequest = xml
        return self.api.search(xml=xml)

    def visibleActiveUsers(self):
        """
        Returns list of all visible active users
        """
        s = Search(module="User")
        s.addCriterion(
            field="UsrStatusBoo",
            operator="equalsField",
            value="True"
        )
        s.validate(mode="search")
        r = self.search(xml=s.toString())
        tree = etree.fromstring(bytes(r.text, "UTF-8"))
        emailL = tree.xpath(
            "/m:application/m:modules/m:module[@name = 'User']/m:moduleItem/m:dataField[@name = 'UsrEmailTxt']/m:value",
            namespaces=NSMAP
        )
        ls = []
        for emailN in emailL:
            if emailN.text != "@smb.spk-berlin.de":
                ls.append(emailN.text)
        return "; ".join(ls)

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
        etree.tostring(tree, pretty_print=True, encoding="unicode")


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
    print (userList)

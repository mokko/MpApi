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
    #NEW INTERFACE
    r = sr.getByGroup(module=module, id=groupId)
    r = sr.getByExhibit(module=module, id=exhibitId)
    r = sr.getByLocation(module=module, id=locId)
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

    #modify data -> not in SAR.py
    
    #helpers                   
    xml = sr.xmlFromFile (path=path)
    sr.toFile(xml=xml, path=path)
    xml = sr.EToString (tree=tree)
    ET = sr.ETfromFile (path=path)
"""

import os  # b/c Pathlib has troubles with windows network paths
from lxml import etree
from pathlib import Path
from MpApi.Search import Search
from MpApi.Client import MpApi
from MpApi.Module import Module

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)


class Sar:  # methods (mosly) in alphabetical order
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

    def _getBy(self, *, module, id, field, since=None):
        """
        Expects module (e.g. Object), id (for that object), fields is a dictionary with a
        set of fields that relevant for the search, since is None or a date; if since is
        not None, search will only list items that are newer than the provided date.

        Sould only get called from getByExhibit, getByGroup, getByLocation
        """
        s = Search(module=module)
        if since is not None:
            s.AND()
        s.addCriterion(
            field=field,
            operator="equalsField",
            value=id,
        )
        if since is not None:
            s.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        s.validate(mode="search")
        return self.api.search(xml=s.toString())

    def getByApprovalGrp(self, *, id, module, since=None):
        """
        ApprovalGrp is the term used in the multimedia module, it's a better label than
        PublicationGrp. So I use it here generically for Freigabe in RIA.

        Gets a set of items depending on the requested module; modules that can be requested
        are Multimedia, Object and Person.

        * id is the ID of the approvalGrp
        * module: requested module (Object, Multimedia, Person)
        * since is either None or a date.

        For Objects
            gets object records in that approval group
        For Multimedia
            gets multimedia records linked to objects in the approval group
        For Person
            gets persons associated with objects in that approval group

        We want to select only records that have Freigabe = Ja, i.e. we need two conditions

        <repeatableGroupItem id="42657392">
            <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
              <vocabularyReferenceItem id="1810139" name="Ja">
                <formattedValue language="en">Ja</formattedValue>
              </vocabularyReferenceItem>
            </vocabularyReference>
            <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
              <vocabularyReferenceItem id="2600647" name="Daten freigegeben für SMB-digital">
                <formattedValue language="en">Daten freigegeben für SMB-digital</formattedValue>
              </vocabularyReferenceItem>
            </vocabularyReference>
        </repeatableGroupItem>
        """

        typeVoc = {
            "Multimedia": "MulObjectRef.ObjPublicationGrp.TypeVoc",
            "Object": "ObjPublicationGrp.TypeVoc",  #  MulApprovalGrp.TypeVoc
            "Person": "PerObjectRef.ObjPublicationGrp.TypeVoc",
        }

        pubVoc = {
            "Multimedia": "MulObjectRef.ObjPublicationGrp.PublicationVoc",
            "Object": "ObjPublicationGrp.PublicationVoc",  #  MulApprovalGrp.TypeVoc
            "Person": "PerObjectRef.ObjPublicationGrp.PublicationVoc",
        }

        query = Search(module=module)
        query.AND()
        query.addCriterion(
            field=str(typeVoc[module]),
            operator="equalsField",
            value=id,
        )
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field=str(pubVoc[module]),
            value="1810139",  # use id? 1810139: yes
        )
        if since is not None:
            s.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        query.validate(mode="search")
        # query.print()
        return self.api.search(xml=query.toString())

    def getByExhibit(self, *, id, module, since=None):
        """
        Gets a set of items related to a certain exhibit depending on the requested module

        * id is the exhibitId,
        * module is the requested module
        * since is None or a date; if a date is provided, gets only items newer than date

        if module is Multimedia
            gets multimedia (records) in exhibit with that id
        if module is Object
            gets objects in exhibit with that $id
        if module is Person
            gets Persons associated with objects that are in exhibit with $id
        if module is Registrar
            gets registrar records of objects in exhibit with $id
        if module is Exhibit
            gets a single exhibit record with that id
        """
        if module == "Exhibition":  # api.getItem should be faster than sar
            return self.api.getItem(module=module, id=id)

        fields = {
            "Multimedia": "MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
            "Object": "ObjRegistrarRef.RegExhibitionRef.__id",
            "Person": "PerObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
            "Registrar": "RegExhibitionRef.__id",
        }
        return self._getBy(module=module, id=id, field=fields[module], since=since)

    def getByGroup(self, *, id, module, since=None):
        fields = {
            "Multimedia": "MulObjectRef.ObjObjectGroupsRef.__id",
            "Object": "ObjObjectGroupsRef.__id",
            "Person": "PerObjectRef.ObjObjectGroupsRef.__id",
        }
        return self._getBy(module=module, id=id, field=fields[module], since=since)

    def getByLocation(self, *, id, module, since=None):
        """
        Gets items of the requested module type by location id.

        * module: reuquested module, possible values are Multimedia, Object or Person
        * id: location id
        * since: None or date; only return items newer than date
        """
        fields = {
            "Multimedia": "MulObjectRef.ObjCurrentLocationVoc",
            "Object": "ObjCurrentLocationVoc",
            "Person": "PerObjectRef.ObjCurrentLocationVoc",
        }
        return self._getBy(module=module, id=id, field=fields[module], since=since)

    def join(self, *, inL):
        """
        Joins the documents in inL to a single document

        Expects a
        * list of zml documents as xml string

        Returns
        * one xml string

        This method is lxml-based, so it works in memory.

        New
        * Old version would add identical moduleItems creating duplicates; new version is
          returning only distinct items. TODO: only keep newer version
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
                            # make a node with the right type
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
                            # test if item exists already
                            newId = int(newItemN.attrib["id"])
                            try:
                                firstET.xpath(
                                    f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem[@id = '{newId}']",
                                    namespaces=NSMAP,
                                )[0]
                            # moduleItem exists already, do nothing
                            # todo: make sure only the newer node survives
                            except:
                                # print ("moduleItem unique, appending")
                                lastModuleN.append(newItemN)

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
                pass  # it is not an error if a file has no items that can be counted

        # print(known_types)
        xml = etree.tostring(firstET, pretty_print=True, encoding="unicode")
        if not xml:
            raise TypeError("Join failed")
        return xml

    def searchBlocks(self, *, xml, size=30):
        """
        Experimenting with a paginated search. Unfinished!

        For a given search query, return the results. If the number of results exceeds
        the block (page) size, return the results in multiple blocks (chunks, pages).

        The paginated or block search is expected to be considerably slower than a
        normal search nice it necessessarily involves more http requests.

        - expects a search request as xml string as well as the block size;
          in production block size should default to 3000 or so. For developing we use
          a lower number.

        - returns a dictionary that is structured as follows
            block = {
                blockNo: 1,  # number of this block (1-based)
                blockSize: 3000, # nominal block size
                last: False,  # not the last block
                offset: 0  # (1-based)
                response: requestObject # payload
                resultsRunning: 3000  # number of results returned so far in this
                                      # and prev. blocks
            }

        We're trying not to use a deterministic algorithm to save some time:
            first request with least amount of fields just to determine the number of results
            further requests for each block with appropriate offset and size values

        Can we dispose of the first request and make the second request the first?
        Yes perhaps but then we only know number of total results when request is done.
        So we would need different return dict structure.

        Sort of a definition:
        A block is the last if the number of returns in a given block is smaller than
        the blockSize or if the query for the next block does not return any results.
        So we may cache one block and look at the next one before we return the first.

        Note to self:
        In order to save cpu time, we might change the interface of MpAPI and SAR and
        pass around xml as etree instead of as string.

        We need a method to see the itemSize of a response
        Search module should allow updating offset value?
        """

    def saveAttachments(self, *, xml, adir, since=None):
        """
        For a set of multimedia moduleItems (provided in xml), download their attachments.
        Attachments are saved to disk with the filename {mulId}.{ext}.

        Typcially will process moduleItems of type multimeida (aka media). Might also work
        on different types.

        Expects
        * xml: a zml string
        * adir: directory to save the attachments to
        * since (optional): xs:date or xs:dateTime; if provided will only get attachments
          of media that are newer than this date

        Returns
        * a set with the paths of the identified attachments; can be counted

        New
        * uses streaming to save memory.
        * downloads only attachments with approval (Typ = "SMB-Freigabe" and Freigabe =
          "Ja")
        * xpath corrected 20211225
        * optional arg since 20211226
        """
        E = etree.fromstring(bytes(xml, "UTF-8"))

        if since is None:
            xpath = """
                /m:application/m:modules/m:module[
                    @name='Multimedia'
                ]/m:moduleItem[
                    @hasAttachments = 'true'
                    and ./m:repeatableGroup[@name = 'MulApprovalGrp']/m:repeatableGroupItem[
                        ./m:vocabularyReference[@name = 'TypeVoc']/m:vocabularyReferenceItem[@name = 'SMB-digital']
                        and ./m:vocabularyReference[@name = 'ApprovalVoc']/m:vocabularyReferenceItem[@name = 'Ja']
                    ]
                ]            
            """
        else:
            print(f" filtering out multimedia records that have changed since {since}")
            # dateTime comparison might not work as expected if number of digits is not equal, e.g. when user
            # provides since with date format (2020-12-12). Perhaps I can check
            xpath = f"""
                /m:application/m:modules/m:module[
                    @name='Multimedia'
                ]/m:moduleItem[
                    @hasAttachments = 'true'
                    and ./m:repeatableGroup[@name = 'MulApprovalGrp']/m:repeatableGroupItem[
                        ./m:vocabularyReference[@name = 'TypeVoc']/m:vocabularyReferenceItem[@name = 'SMB-digital']
                        and ./m:vocabularyReference[@name = 'ApprovalVoc']/m:vocabularyReferenceItem[@name = 'Ja']
                    ]
                    and ./m:systemField[
                        @name = '__lastModified'
                        and translate(m:value,'-:T. ','') > translate('{since}','-:T. ','')
                    ]
                ]
            """
        itemsL = E.xpath(xpath, namespaces=NSMAP)
        print(xpath)

        print(
            f" xml has {len(itemsL)} records with attachment=True and Freigabe[@typ='SMB-Digital'] = Ja"
        )

        positives = set()  # future return value

        for itemN in itemsL:
            itemA = itemN.attrib  # A for attribute
            mmId = itemA["id"]
            # Why do i get suffix from old filename? Is that really the best source?
            # Seems that it is. I see no other field in RIA
            # assuming that there can be only one
            fn_old = itemN.xpath(
                "m:dataField[@name = 'MulOriginalFileTxt']/m:value/text()",
                namespaces=NSMAP,
            )[0]
            fn = mmId + Path(fn_old).suffix
            mmPath = Path(adir).joinpath(fn)
            # print(f"POSITIVE {mmPath}")
            positives.add(mmPath)
            # only d/l if doesn't exist yet
            if not mmPath.exists():
                print(f" getting {mmPath}")
                self.api.saveAttachment(module="Multimedia", id=mmId, path=mmPath)
        return positives

    def search(self, *, xml):
        """
        Send a request to the api and return the response. Expects an search as xml
        string in xml. (Same as in MpApi).
        """
        return self.api.search(xml=xml)

    #
    # Helper
    #
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
    getattr(s, args.cmd)(args.args)  # untested

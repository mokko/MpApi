"""
Sar stands for search and response. It's a higher level interface on top of 
MpApi that bundles multiple requests in one method, typically a search and a 
response. 

I introduce it mainly to clean up the code of the Mink class, so that Mink 
has to deal less with xml and Sar.py can be tested easier. (Conversely, that 
means that mink parses DSL config file, writes files and logs report.) 

This is a new version of Sar that typically returns a Module object as a 
requests reponse.  

USAGE
    import Sar from mpapi.sar
    import Search from mpapi.search
    import Module from mpapi.module
    sr = Sar(baseURL=baseURL, user=user, pw=pw)

    #get stuff from single ids; returns request object
    m = sr.getByGroup(module=module, Id=groupId)
    m = sr.getByExhibit(module=module, Id=exhibitId)
    m = sr.getByLocation(module=module, Id=locId)
    m = sr.getByApprovalGrp(module=module, Id=approvalId)

    #search
    query = Search()
    query.addCriterion(
            field=field,
            operator="equalsField",
            value=Id,
        )
    m = sr.search(query=query) # returns Module object now

    # attachments
    sr.saveAttachments(data=Module(file="a.xml"), adir=dir) 
        # for moduleItems in data download attachments and save as
        #     adir/{mulId}.{ext} 
        # only download media with smbfreigabe

    # moved to Module now
    m.clean()    # cleans m as a side-effect
    m.validate() # dies if doesn't validate
    m3 = m1 + m2 # distinct join/add 

NEW
* we're slowly transitioning from 
   id -> Id -> ID
   module -> mtype
2022-01
* more abstraction by returning Module, simplification by removing redundant helper methods
* type hints added (again)
* down to 300 some lines where half are docstrings. Yay!
2021-12
* some methods removed since they didn't add anything to basic mpapi.client 
  (definition, search, getItem)
* some methods renamed, b/c they are useful and dont need to stay private 
  (dropUUID, dropRepeatableGroup)
* avoid capital letters in package names to be more conformist/pythonic

THE SINCE PARAMETER
The since parameter expects typical xs:dateTime format,e.g. 
    2021-10-14T07:40:29Z
but internally it's transformed to a number to compare it in xpath 1.0
    20211014074029 
then it's reduced to a 14 digit number (resolution seconds) by cutting off 
additional numbers (referencing fractions of seconds).
"""

import os  # b/c Pathlib has troubles with Windows network paths
from lxml import etree
from mpapi.module import Module
from mpapi.search import Search
from mpapi.client import MpApi
from mpapi.module import Module
from pathlib import Path

# from typing import set
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)


class Sar:
    def __init__(self, *, baseURL: str, user: str, pw: str) -> None:
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.user = user

    def _getBy(self, *, module: str, Id: int, field: str, since=None) -> Module:
        """
        Expects
        * requested target module type (e.g. "Object"),
        * Id (for that object),
        * field: a dictionary with a set of fields that are relevant for the
          search,
        * since is None or a dateTime; if since is not None, search will only
          look for items that are newer than the provided date.

        Should only get called from getByExhibit, getByGroup, getByLocation
        """
        query = Search(module=module)
        if since is not None:
            query.AND()
        query.addCriterion(
            field=field,
            operator="equalsField",
            value=Id,
        )
        if since is not None:
            query.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        return self.api.search2(query=query)

    def checkApproval(self, *, ID: int, mtype: str) -> bool:
        """
        For a record, check if it has an approval for SMB-Digital. Currently only
        works for module type Object.

        Returns True or False.
        """
        if mtype != "Object":
            raise ValueError("ERROR: checkApproval currently only works for Object")

        # 2600647 = SMB-Digital
        m = self.api.getItem2(mtype=mtype, ID=ID)
        r = m.xpath(
            f"""/m:application/m:modules/m:module[
                @name = '{mtype}']/m:moduleItem[
                @id = {ID}]/m:repeatableGroup[
                @name = 'ObjPublicationGrp']/m:repeatableGroupItem[
                    m:vocabularyReference[@name='PublicationVoc']/m:vocabularyReferenceItem[@name='Ja'] 
                    and m:vocabularyReference[@name='TypeVoc']/m:vocabularyReferenceItem[@id = 2600647]
                ]"""
        )
        if len(r) > 0:
            return True
        else:
            return False

    def getByApprovalGrp(self, *, Id: int, module: str, since: str = None) -> Module:
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

        typeVoc: dict = {
            "Multimedia": "MulObjectRef.ObjPublicationGrp.TypeVoc",
            "Object": "ObjPublicationGrp.TypeVoc",  #  MulApprovalGrp.TypeVoc
            "Person": "PerObjectRef.ObjPublicationGrp.TypeVoc",
        }

        pubVoc: dict = {
            "Multimedia": "MulObjectRef.ObjPublicationGrp.PublicationVoc",
            "Object": "ObjPublicationGrp.PublicationVoc",  #  MulApprovalGrp.TypeVoc
            "Person": "PerObjectRef.ObjPublicationGrp.PublicationVoc",
        }

        query = Search(module=module)
        query.AND()
        query.addCriterion(
            field=str(typeVoc[module]),
            operator="equalsField",
            value=Id,
        )
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field=str(pubVoc[module]),
            value="1810139",  # use id? 1810139: yes
        )
        if since is not None:
            query.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        return self.api.search2(query=query)

    def getByExhibit(self, *, Id: int, module: str, since: str = None) -> Module:
        """
        Gets a set of items related to a certain exhibit depending on the
        requested module.

        * id is an exhibitId,
        * module is the requested module (of the results)
        * since is None or a date; if a date is provided, gets only items newer
          than date

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
            return self.api.getItem(module=module, id=Id)

        fields: dict = {
            "Multimedia": "MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
            "Object": "ObjRegistrarRef.RegExhibitionRef.__id",
            "Person": "PerObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
            "Registrar": "RegExhibitionRef.__id",
        }
        return self._getBy(module=module, Id=Id, field=fields[module], since=since)

    def getByGroup(self, *, Id: int, module: str, since: str = None) -> Module:
        fields: dict = {
            "Multimedia": "MulObjectRef.ObjObjectGroupsRef.__id",
            "Object": "ObjObjectGroupsRef.__id",
            "Person": "PerObjectRef.ObjObjectGroupsRef.__id",
        }
        return self._getBy(module=module, Id=Id, field=fields[module], since=since)

    def getByLocation(self, *, Id: int, module: str, since: str = None) -> Module:
        """
        Gets items of the requested module type by location id.

        * module: reuquested module, possible values are Multimedia, Object or Person
        * id: location id
        * since: None or date; only return items newer than date
        """
        fields: dict = {
            "Multimedia": "MulObjectRef.ObjCurrentLocationVoc",
            "Object": "ObjCurrentLocationVoc",
            "Person": "PerObjectRef.ObjCurrentLocationVoc",
        }
        return self._getBy(module=module, Id=Id, field=fields[module], since=since)

    def saveAttachments(self, *, data: Module, adir: Path, since=None) -> set[Path]:
        """
        For a set of multimedia moduleItems (provided in xml), download their attachments.
        Attachments are saved to disk with the filename {mulId}.{ext}.

        Expects
        * data: as a Module object
        * adir: directory to save the attachments to
        * since (optional): xs:date or xs:dateTime; if provided will only get attachments
          of media that are newer than this date

        Returns
        * a set with the paths of the identified attachments; can be counted

        Caveats
        * is restricted to assets that have SMB-Dgital approval; now I want also none-restricted
          ones.
        * works only on multimedia items; other module types' items are ignored -> for now that is
          an acceptable limitation. Why would I need attachments from other mtypes atm.
        * uses streaming to save memory.

        New
        * downloads only attachments with approval (Typ = "SMB-Freigabe" and Freigabe =
          "Ja")
        * xpath corrected 20211225
        * optional arg since 20211226
        """
        if since is None:
            xp = """
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
            print(f" filtering multimedia records that have changed since {since}")
            """
            dateTime comparison might not work as expected if number of digits is not equal, e.g. when user
            provides since with date format (2020-12-12). Perhaps I can check
            Possible values from the data
            1970-01-01 00:00:00.0 -> 1970-01-01 00:00:00.0 

            2021-09-13 11:08:51.251
            2018-05-31T00:00:00Z
            2021-10-14T07:40:29Z
            
            I define a standardized form which has 14 digits minimum (8 + 6), i.e. one digit after the period
            where should this rewriting of the since argument took place? Not here.
            """

            xp = f"""
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
                        and substring(translate(m:value,'-:.TZ ',''),0, 14) > 
                        substring(translate('{since}','-:.TZ ',''), 0, 14)
                    ]
                ]
            """
        # print(xp)
        print(
            f" xml has {len(itemsL)} records with attachment=True and Freigabe[@typ='SMB-Digital'] = Ja"
        )
        return self._saveAttachments(moduleItemL=data.xpath(xp), adir=adir, since=since)

    def _saveAttachments(
        self, *, moduleItemL: list, adir: Path, since=None
    ) -> set[Path]:
        """
        the L in moduleItemL stands for nodeList. So it expects a list of nodes instead of

        a whole document.

        Apparently, what I want is to split up one long xpath expression into multiple

        nodeList = document.xpath(A)
        nodeList2 = nodeList.xpathNL(B)
        """

        # Why do i get suffix from old filename? Is that really the best source?
        # Seems that it is. I see no other field in RIA
        positives = set()
        for itemN in moduleItemL:
            # itemA = itemN.attrib
            # mmId = itemA["id"]
            mmId = itemN.attrib["id"]
            fn_old = itemN.xpath(
                "m:dataField[@name = 'MulOriginalFileTxt']/m:value/text()",
                namespaces=NSMAP,
            )[
                0
            ]  # assuming that there can be only one
            fn = mmId + Path(fn_old).suffix
            mm_fn = Path(adir).joinpath(fn)
            positives.add(mm_fn)
            if not mm_fn.exists():  # only d/l if doesn't exist yet
                print(f" getting {mm_fn}")
                self.api.saveAttachment(module="Multimedia", id=mmId, path=mm_fn)
            else:
                print(f" {mm_fn} exists already")
        return positives

    def search(self, *, query: Search) -> Module:
        """Modern search that expects and returns objects"""
        return self.api.search2(query=query)

    def xpathNL(self, *, path: str, nodeList: list) -> list:
        """Like xpath, but expects a nodeList; returns a nodeList.

        UNTESTED
        """
        new = list()
        for node in nodeList:
            new.expand(node.xpath(path, namespaces=NSMAP))
        return new

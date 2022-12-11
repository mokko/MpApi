"""
MpApi - Unofficial Open Source Client for MuseumPlus MpRIA Version 2

Experimental - Not yet tested

This is another iteration of the interface in which I take more liberties in 
order achieve a plausible, consistent and practical interface.

USAGE
    from mpapi.client2 import Client2
    c = Client2(baseURL=baseURL, user=user, pw=pw)
    m = c.getDefinition(modType="Object")
    
Consistent Interface
    modType refers to module/@name so perhaps should be called modName
    tType refers to module/@name of the target, e.g. the search results
    
    should we call modType modType instead to be more consistent?
    see modItemId
"""

from requests.auth import HTTPBasicAuth
from lxml import etree  # type: ignore
from mpapi.client import MpApi
from mpapi.search import Search
from mpapi.module import Module
from typing import Any, Union
import requests

ETparser = etree.XMLParser(remove_blank_text=True)


class Client2:
    def __init__(
        self, *, baseURL: str, user: str, pw: str, acceptLang: str = "de"
    ) -> None:
        self.appURL = baseURL + "/ria-ws/application"
        self.session = requests.Session()
        self.session.auth = (user, pw)
        self.session.headers.update(
            {
                "Content-Type": "application/xml",
                "Accept": "application/xml;charset=UTF-8",
                "Accept-Language": acceptLang,
            }
        )
        self.client = MpApi(baseURL=baseURL, user=user, pw=pw, acceptLang=acceptLang)

    #
    # B REQUESTS WITH module.xsd response
    #
    # B.1 DATA DEFINITIONs
    #
    def getDefinition(self, *, modType: str = None) -> Module:
        """
        Return the data definition for a single or all modules
        """
        r = self.client.getDefinition(module=modType)
        return Module(xml=r.text)

    def runSavedQuery(
        self, *, searchId: int, tType: str = "Object", limit: int = -1, offset: int = 0
    ):  # -> ET
        """
        Higher level version of runSavedQuery where you specify limit and
        offset with parameters and return result as Module object.

        Expects
        - ID: integer
        - Type: target type (module type of the results)
        - limit
        - offset
        Returns
        - result document as etree object

        New
        - in a previous version, this method was restricted to Object module
          (as tType)
        - previous version used to return etree Objects instead of Module

        """
        xml = f"""
        <application 
            xmlns="http://www.zetcom.com/ria/ws/module/search" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search 
            http://www.zetcom.com/ria/ws/module/search/search_1_6.xsd">
            <modules>
              <module name="{tType}">
                <search limit="{limit}" offset="{offset}" />
              </module>
            </modules>
        </application>
        """

        q = Search(fromString=xml)
        q.validate(mode="search")

        print(xml)
        r = self.client.runSavedQuery(id=searchId, mtype=tType, xml=q.toString())
        # return etree.fromstring(r.content, ETparser)
        return Module(xml=r.text)

    #
    # B.2 SEARCHING
    #

    def search(self, *, query: Search) -> Module:
        """
        Perform a search, but with modern parameters and return values

        EXPECTS
        * Search object
        RETURNS
        * Module object
        """
        query.validate(mode="search")
        r = self.client._search(queryET=query.toET())
        return Module(xml=r.text)

    """
    B.3 WHOLE MODULE ITEMS
    r = createItem2(modtype="Object", data=m)
    m = getItem2(modtype="Object", modItemId=123)
    r = updateItem2(modtype="Object", data=m)
    r = deleteItem2(modtype="Object", modItemId=123)
    """

    def getItem(self, *, modType: str, modItemId: int) -> Module:
        """
        Like getItem, but with modern parameters and returns Module object.
        """
        r = self.client.getItem(module=modType, id=modItemId)
        return Module(xml=r.text)

    def createItem(self, *, modType: str, data: Module) -> Module:
        """
        Like createItem, but with modern parameters and returns Module object.

        DESIGN
        - Alternatively, createItem could expect xml as etree, but that wouldn't
          save anything, so no.

        r = self.createItem(module=mtype, xml=data.toString())
        data.toString()
        """
        # why are we not using Module's toString method?
        ET = data.toET()
        xml = etree.tostring(ET, pretty_print=True)
        r = self.client.createItem(module=mtype, xml=xml)
        return Module(xml=r.text)

    def updateItem(
        self, *, modType: str, modItemId: int, data: Module
    ) -> requests.Response:
        """
        v2 with other param names and data provided as Module object.
        """
        xml = data.toString()
        # print(xml)
        return self.client.updateItem(module=modType, id=modItemId, xml=xml)

    def deleteItem(self, *, modType: str, modItemId: int) -> requests.Response:
        """What is the return value?"""
        return self.client.deleteItem(module=modType, id=modItemId)

    """
    B.4 FIELDs
    r = updateField2(mtype="Object", ID=123, dataField="OgrNameTxt", value="ein Titel")

    Read: Just get all fields instead of one or mark fields you want in the search to 
    get mostly that one.
    
    How do I create and delete a field? There don't seem to be specific endpoints
    """

    def updateField(
        self, *, modType: str, modItemId: int, dataField: str, value: str
    ) -> requests.Response:
        """Higher order version of updateField which creates its own xml

        Note according to newer practice ID is spelled with capital letters
        here on purpose and parameter ´module´ is referred here as mtype as it
        is less ambiguous.

        Does the API return anything meaningful? HTTP response, I guess
        """

        m = Module()
        mm = m.module(name=mtype)
        item = m.moduleItem(parent=mm, ID=ID)
        m.dataField(parent=item, name=dataField, value=value)
        m.validate()
        # m.toFile(path="upField.debug.xml")  # needs to go later
        return self.client.updateField(
            module=modType, id=modItemId, dataField=dataField, xml=m.toString()
        )

    """
    B.5 REPEATABLE GROUPS and module|vocabulary references
    createReference (no createReference2 yet)
    createRepeatableGroup 
    """

    def createReferenceItem(
        self, *, modType: str, modItemId: int, grpName: str, grpId: int, refName: str
    ):
        return self.client.createReference(
            module=modType,
            id=modItemId,
            reference=grpName,
            groupId=grpId,  # refName missing
        )

    def createGrpItem(
        self, *, modType: str, modItemId: int, grpref: str, xml: str
    ) -> requests.Response:  # nodes is lxml.etree
        """
        I believe this creates a new rGrpItem for an existing rGrp or an vRefItem/mRefItem for
        existing references.

        The first time I am using this, xml as str is more convenient than ET's nodes. Let's see
        if this is the case in the future as well.
        """
        # xml = etree.tostring(node)
        return self.client.createRepeatableGroup(
            module=modType, id=modItemId, repeatableGroup=grpref, xml=xml
        )

    def addModRefItem3(
        self, *, modType: str, modItemId: int, refName: str, refIds: list
    ) -> requests.Response:
        """
        Like addModRefItem2, but accepts a list of refIds. Untested.
        """
        xml = f"""<application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{mtype}">
              <moduleItem id="{modItemId}">
                <moduleReference name="{refName}" targetModule="Object" multiplicity="M:N"/>
              </moduleItem>
            </module>
          </modules>
        </application>"""
        docN = ET.xml(xml)
        modRef = docN.xpath("//m:moduleReference", namespaces=NSMAP)[0]
        for refId in refIds:
            etree.SubElement(
                modRef, "m:moduleReferenceItem", {"moduleItemId": refId}, NSMAP
            )
        return self.createGrpItem(
            mtype=modType, ID=modItemId, grpref=refName, xml=docN.tostring()
        )  # encoding="UTF8"

    def updateRepeatableGroupItem(
        self, *, modType: str, modItemId: int, refId: int, grpName: str, node
    ) -> requests.Response:
        xml = etree.tostring(node)
        return updateRepeatableGroup(
            module=mtype,
            id=ID,
            referenceId=referenceId,
            repeatableGroup=repeatableGroup,
            xml=xml,
        )

    #
    # D RESPONSE orgunit
    #
    def getOrgUnits(self, *, modType: str) -> Module:
        """
        Returns writable OrgUnits for a specific module type. Defaults to ObjectGroup
        at the moment.

        Used to write debug file to disk.
        """
        r = self.client.getOrgUnits(module=modType)
        return Module(xml=r.text)

"""
MpApi - Unofficial Open Source Client for MuseumPlus MpRIA Version 2

Experimental - Not yet tested

USAGE

"""

from requests.auth import HTTPBasicAuth
from lxml import etree  # type: ignore
from mpapi.client import Client
from mpapi.search import Search
from mpapi.module import Module
from typing import Any, Union
import requests

ETparser = etree.XMLParser(remove_blank_text=True)


class client2:
    def __init__(self, *, baseURL: str, user: str, pw: str) -> None:
        self.appURL = baseURL + "/ria-ws/application"
        self.session = requests.Session()
        self.session.auth = (user, pw)
        self.session.headers.update(
            {
                "Content-Type": "application/xml",
                "Accept": "application/xml;charset=UTF-8",
                "Accept-Language": "de",
            }
        )
        self.client = Client(baseURL=baseURL, user=user, pw=pw)

    #
    # B REQUESTS WITH module.xsd response
    #
    # B.1 DATA DEFINITIONs
    #
    def getDefinition(self, *, mType: str = None) -> requests.Response:
        """
        Return the data definition for a single or all modules
        """
        return self.client.getDefinition(module=mType)

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
          (as Type).

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

        print("-----------------------")
        print(xml)
        r = self.client.runSavedQuery(id=searchId, mtype=tType, xml=q.toString())
        return etree.fromstring(r.content, ETparser)

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
        m = Module(xml=r.text)
        # print (f"ACTUAL SIZE: {m.actualSize()}")
        return m

    """
    B.3 WHOLE MODULE ITEMS
    r = createItem2(mtype="Object", data=m)
    m = getItem2(mtype="Object", ID=123)
    r = updateItem2(mtype="Object", data=m)
    r = deleteItem2(mtype="Object", ID=123)
    """

    def getItem(self, *, mType: str, modItemId: int) -> Module:
        """
        Like getItem, but with modern parameter names and returns Module
        object.
        """
        r = self.client.getItem(module=mtype, id=ID)
        return Module(xml=r.text)

    def createItem(self, *, mType: str, data: Module) -> Module:
        """
        Like createItem, but with modern parameters and returns Module
        object.

        DESIGN
        - Alternatively, createItem2 could expect xml as etree, but that wouldn't
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
        self, *, mType: str, modItemId: int, data: Module
    ) -> requests.Response:
        """
        v2 with other param names and data provided as Module object.
        """
        xml = data.toString()
        # print(xml)
        return self.client.updateItem(module=mType, id=modItemId, xml=xml)

    def deleteItem(self, *, mType: str, modItemId: int) -> requests.Response:
        """What is the return value?"""
        return self.client.deleteItem(module=mType, id=modItemId)

    """
    B.4 FIELDs
    r = updateField2(mtype="Object", ID=123, dataField="OgrNameTxt", value="ein Titel")

    Read: Just get all fields instead of one or mark fields you want in the search to 
    get mostly that one.
    
    How do I create and delete a field? There don't seem to be specific endpoints
    """

    def updateField(
        self, *, mType: str, modItemId: int, dataField: str, value: str
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
            module=mType, id=modItemId, dataField=dataField, xml=m.toString()
        )

    """
    B.5 REPEATABLE GROUPS and module|vocabulary references
    createReference (no createReference2 yet)
    createRepeatableGroup 
    """

    def createReferenceItem(
        self, *, mType: str, modItemId: int, grpName: str, grpId: int, refName: str
    ):
        return self.client.createReference(
            module=mType,
            id=modItemId,
            reference=grpName,
            groupId=grpId,  # refName missing
        )

    def createGrpItem(
        self, *, mType: str, modItemId: int, grpref: str, xml: str
    ) -> requests.Response:  # nodes is lxml.etree
        """
        I believe this creates a new rGrpItem for an existing rGrp or an vRefItem/mRefItem for
        existing references.

        The first time I am using this, xml as str is more convenient than ET's nodes. Let's see
        if this is the case in the future as well.
        """
        # xml = etree.tostring(node)
        return self.client.createRepeatableGroup(
            module=mType, id=modItemId, repeatableGroup=grpref, xml=xml
        )

    def addModRefItem3(
        self, *, mType: str, modItemId: int, refName: str, refIds: list
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
            mtype=mType, ID=modItemId, grpref=refName, xml=docN.tostring()
        )  # encoding="UTF8"

    def updateRepeatableGroupItem(
        self, *, mType: str, modItemId: int, refId: int, grpName: str, node
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
    def getOrgUnits(self, *, mType: str) -> Module:
        r = self.client.getOrgUnits(module=mType)
        return Module(xml=r.text)

"""
MpApi - MuseumPlus API Client  

USAGE
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", id="12345")
    key = api.getSessionKey()
    api.toFile(response=r, path="path/to/file.xml")

Which are the modules our instance knows
    - _SystemMessage, SystemCopyScheme, _SystemJob
    - Accessory, Address, AddressGroup, CollectionActivity, Conservation, Contract
    - Datasource, DefDimension, DefLiterature, Exhibition, Event, Function, FunctionGenerator
    - InventoryNumber, Literature, Movement, Multimedia, MultimediaGroup, Object, ObjectGroup
    - Ownership, OrganisationUnit, Place, Parameter, Registrar, Person, Search, Task, Template
    - User, UserGroup

ENCODING SCHEME
    - RIA dishes out and requests UTF-8; mpapi should do that too

SEE ALSO
    http://docs.zetcom.com/ws
"""

# import logging
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from lxml import etree  # type: ignore
from mpapi.search import Search
from mpapi.module import Module
from typing import Any, Union
import requests

ET: Any
ETparser = etree.XMLParser(remove_blank_text=True)


class MpApi:
    def __init__(self, *, baseURL: str, user: str, pw: str) -> None:
        #self.baseURL = baseURL
        #self.appURL = baseURL + "/ria-ws/application"
        #self.auth = HTTPBasicAuth(user, pw)
        #headers: CaseInsensitiveDict = CaseInsensitiveDict()
        #headers["Content-Type"] = "application/xml"
        #headers["Accept"] = "application/xml;charset=UTF-8"
        #headers["Accept-Language"] = "de"
        #self.headers = headers

        s = requests.Session()
        s.auth = (user, pw)
        s.headers.update({
            'Content-Type': 'application/xml',
            'Accept': 'application/xml;charset=UTF-8',
            'Accept-Language': 'de'
        })
        self.session = s

    def _delete(self, url):
        r = self.session.delete(url)
        r.raise_for_status()
        # print(f"DEL ENC {r.encoding}")
        # r.encoding = "utf-8"
        return r

    def _get(self, url, *, params=None):
        if params is None:
            r = self.session.get(url)
        else:
            r = self.session.get(url, params=params)
        r.raise_for_status()
        # print(f"GET ENC {r.encoding}")
        # r.encoding = "utf-8"
        return r

    def _post(self, url, *, data):
        r = self.session.post(url, data=data)
        r.raise_for_status()
        # print(f"POST ENC {r.encoding}")
        # r.encoding = "utf-8"
        return r

    def _put(self, url, *, data):
        r = self.session.put(url, data=xml)
        r.raise_for_status()
        # print(f"PUT ENC {r.encoding}")
        # r.encoding = "utf-8"
        return r

    def _search(self, *, queryET) -> requests.Response:
        """
        A version of the search method that expects the query as etree document
        and returns requests response.
        """

        mtype = queryET.xpath(
            "/s:application/s:modules/s:module/@name",
            namespaces={"s": "http://www.zetcom.com/ria/ws/module/search"},
        )[0]
        if not mtype:
            raise TypeError("Unknown module")
        url = f"{self.appURL}/module/{mtype}/search"

        return self._post(
            url,
            data=etree.tostring(queryET),  # encoding="unicode"
        )

    #
    # A SESSION
    #
    def getSessionKey(self) -> str:  # should be int?
        """
        GET http://.../ria-ws/application/session
        """
        url = self.appURL + "/session"
        r = self._get(url)
        tree = self.ETfromString(xml=r.text)

        key = tree.xpath(
            "/s:application/s:session/s:key/text()",
            namespaces={"s": "http://www.zetcom.com/ria/ws/session"},
        )
        return key

    #
    # B REQUESTS WITH module.xsd response
    #
    # B.1 DATA DEFINITIONs
    #
    def getDefinition(self, *, module: str = None) -> requests.Response:
        """
        Retrieve the data definition of a single or of all modules
        GET http://.../ria-ws/application/module/{module}/definition/
        GET http://.../ria-ws/application/module/definition/

        returns a request containing the module definition for specified module
        or all modules if no module is specified.
        """

        if module is None:
            url = self.appURL + "/module/definition"
        else:
            url = self.appURL + "/module/" + module + "/definition"

        return self._get(url)

    #
    # B.2 SEARCHING
    #
    def runSavedQuery(self, *, id: int, mtype: str, xml: str) -> requests.Response:
        """
        Run a pre-existing saved search
        POST http://.../ria-ws/application/module/{module}/search/savedQuery/{__id}

        N.B. / Caveats
        - Currently only queries targeting the Object module are supported! Ideally,
          client.py would extract that piece of information from the query.
        - api does not support since. If you need that include that since date in your
          RIA query.

        Quote from http://docs.zetcom.com/ws/:
        A request body must be provided, in order to control the paging. For example:

        <application
            xmlns="http://www.zetcom.com/ria/ws/module/search"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_4.xsd">
            <modules>
              <module name="Object">
                <search limit="10" offset="0" />
              </module>
            </modules>
        </application>
        """
        url = f"{self.appURL}/module/{mtype}/search/savedQuery/{id}"
        return self._post(url, data=xml)

    def runSavedQuery2(
        self, *, ID: int, Type: str = "Object", limit: int = -1, offset: int = 0
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
              <module name="{Type}">
                <search limit="{limit}" offset="{offset}" />
              </module>
            </modules>
        </application>
        """

        q = Search(fromString=xml)
        q.validate(mode="search")

        print("-----------------------")
        print(xml)
        r = self.runSavedQuery(id=ID, mtype=Type, xml=q.toString())
        return etree.fromstring(r.content, ETparser)

    def search(self, *, xml: str) -> requests.Response:
        """
        Perform an ad-hoc search for modules items
        POST http://.../ria-ws/application/module/{mtype}/search/

        New: We're getting the mtype from the xml to avoid errors.
        """
        queryET = self.ETfromString(xml=xml)
        return self._search(queryET=queryET)

    def search2(self, *, query: Search) -> Module:
        """
        Perform a search, but with modern parameters and return values

        EXPECTS
        * Search object
        RETURNS
        * Module object
        """
        query.validate(mode="search")
        r = self._search(queryET=query.toET())
        m = Module(xml=r.text)
        # print (f"ACTUAL SIZE: {m.actualSize()}")
        return m

    #
    # B.3 WHOLE MODULE ITEMS
    #
    def getItem(self, *, module: str, id: int) -> requests.Response:
        """
        Get a single module item
        GET http://.../ria-ws/application/module/{module}/{__id}

        URL parameters (e.g. &loadAttachment=true):

        loadAttachment | type: boolean | default: false | load attachment if exists
        loadThumbnailExtraSmall | type: boolean | default: false | load extra small thumbnail
        loadThumbnailSmall | type: boolean | default: false | load small thumbnail
        loadThumbnailMedium | type: boolean | default: false | load medium thumbnail
        loadThumbnailLarge | type: boolean | default: false | load large thumbnail
        loadThumbnailExtraLarge | type: boolean | default: false | load extra large thumbnail
        """
        return self._get(f"{self.appURL}/module/{module}/{id}")

    def getItem2(self, *, mtype: str, ID: int) -> Module:
        """
        Like getItem, but with modern parameter names and returns Module
        object.
        """
        r = self.getItem(module=mtype, id=ID)
        return Module(xml=r.text)

    def createItem(self, *, module: str, xml: str) -> requests.Response:
        """
        Create new module item or items.
        POST http://.../ria-ws/application/module/{module}

        Is there a return value? I would like to know the id
        """
        url = self.appURL + "/module/" + module
        return self._post(url, data=xml)

    def createItem2(self, *, mtype: str, data: Module) -> Module:
        """
        Like createItem, but with modern parameters and returns Module
        object.

        DESIGN
        - Alternatively, createItem2 could expect xml as etree, but that wouldn't
          save anything, so no.

        r = self.createItem(module=mtype, xml=data.toString())
        data.toString()
        """
        ET = data.toET()
        xml = etree.tostring(ET, pretty_print=True)
        r = self.createItem(module=mtype, xml=xml)
        return Module(xml=r.text)

    def updateItem(self, *, module: str, id: int, xml: str) -> requests.Response:
        """
        Update all fields of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}
        """
        url = f"{self.appURL}/module/{module}/{id}"
        return self._put(url, data=xml)

    def deleteItem(self, *, module: str, id: int) -> requests.Response:
        """
        Delete a module item
        DELETE http://.../ria-ws/application/module/{module}/{__id}
        """
        url = f"{self.appURL}/module/{module}/{id}"
        return self._delete(url)

    #
    # B.4 FIELDs
    #
    def updateField(
        self, *, module: str, id: int, dataField: str, xml: str
    ) -> requests.Response:
        """
        Update a single field of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}/{dataField}

        NB: We dont need a createField method since simple dataFields are always created.
        """
        url = f"{self.appURL}/module/{module}/{id}/{dataField}"
        return self._put(url, data=xml)

    def updateField2(
        self, *, mtype: str, ID: int, dataField: str, value: str
    ) -> requests.Response:
        """Higher order version of updateField which creates its own xml

        Note according to newer practice ID is spelled with capital letters
        here on purpose and parameter ´module´ is referred here as mtype as it
        is less ambiguous.

        Does the API return anything  meaningful?
        """

        m = Module()
        mm = m.module(name=mtype)
        item = m.moduleItem(parent=mm, ID=ID)
        m.dataField(parent=item, name=dataField, value=value)
        m.validate()
        # m.toFile(path="upField.debug.xml")  # needs to go later
        return self.updateField(
            module=mtype, id=ID, dataField=dataField, xml=m.toString()
        )

    #
    # B.5 REPEATABLE GROUPS
    #
    def createReference(
        self,
        *,
        module: str,
        id: int,
        groupId: int,
        reference: str,
        repeatableGroup: str,
        xml: str,
    ) -> requests.Response:
        """
        Add a reference to a reference field within a repeatable group
        POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}

        Remember that xml is different during downloads than for uploads.
        Upload xml omitts, for example, formattedValues.
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{groupId}/{reference}"
        return self._post(url, data=xml)

    def createRepeatableGroup(
        self, *, module: str, id: int, repeatableGroup: str, xml: str
    ) -> requests.Response:
        """
        Create repeatable group / reference
        #POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}
        eg. https://<host>/<application>/ria-ws/application/module/Address/29011/AdrContactGrp
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}"
        return self._post(url, data=xml)

    def updateRepeatableGroup(
        self, *, module: str, id: int, referenceId: int, repeatableGroup: str, xml: str
    ) -> requests.Response:
        """
        Update all fields of repeatable groups / references
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}"
        # xml = xml.encode()
        return self._put(url, data=xml)

    def updateFieldInGroup(
        self,
        *,
        module: str,
        id: int,
        referenceId: int,
        dataField: str,
        repeatableGroup: str,
        xml: str,
    ) -> requests.Response:
        """
        Update a single data field of a repeatable group / reference
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}/{dataField}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}/{dataField}"
        return self._put(url, data=xml)

    def deleteRepeatableGroup(
        self, *, module: str, id: int, referenceId: str, repeatableGroup: str
    ) -> requests.Response:
        """
        Delete a complete repeatable group / reference
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}"
        return self._delete(url)

    def deleteReferenceInGroup(
        self,
        *,
        module: str,
        id: int,
        groupId: str,
        reference: str,
        referenceId: int,
        repeatableGroup: str,
    ) -> requests.Response:
        """
        Delete a reference contained within a repeatable group
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{groupId}/{reference}/{referenceId}"
        return self._delete(url)

    #
    # C ATTACHMENTs AND THUMBNAILs
    #

    def getAttachment(self, *, module: str, id: int) -> requests.Response:
        """
        GET http://.../ria-ws/application/module/{module}/{__id}/attachment
        Get an attachment for a specified module item. You should use the GET method with
        application/octet-stream Header (described below) that returns the attachment in
        binary form. The binary file format approach consumes less bandwidth than the xml
        approach cause of the Base64 encoding that becomes necessary with xml.

        The request will return status code 200 (OK) if the syntax of the request was
        correct. The content will be send using the MIME type application/octet-stream
        and the Content-disposition header with a suggested filename.

        """

        url = f"{self.appURL}/module/{module}/{id}/attachment"

        #headers = self.headers  # is this a true copy?
        #oldAccept = self.headers["Accept"]
        #self.headers["Accept"] = "application/octet-stream"
        r = self._get(url, params={'Accept': 'application/octet-stream'})
        #self.headers["Accept"] = oldAccept
        return r

    def saveAttachment(self, *, module: str = "Multimedia", id: int, path: str) -> int:
        """
        Streaming version of getAttachment that saves attachment directly to disk.

        Expects
        - module: module type (e.g. "Multimedia"),
        - id: item id in specified module (int)
        - path: filename/path to save attachment to
        to.

        Returns id if successful.

        Note: There is a similar saveAttachments in Sar.py that calls this one.
        """
        url = f"{self.appURL}/module/{module}/{id}/attachment"

        #headers = self.headers  # is this a true copy?
        #oldAccept = self.headers["Accept"]
        #self.headers["Accept"] = "application/octet-stream"
        r = self._get(url, stream=True, headers={'Accept': 'application/octet-stream'})
        r.raise_for_status()  # todo: replace with r.raise_for_status()?

        # exception: not using _get
        with self.session.get(url, stream=True, headers={'Accept': 'application/octet-stream'}) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        #self.headers["Accept"] = oldAccept
        return id

    def getThumbnail(self, *, module: str, id: int, path: str) -> requests.Response:
        """
        Get the thumbnail of a module item attachment
        GET http://.../ria-ws/application/module/{module}/{__id}/thumbnail
        """
        url = f"{self.appURL}/module/{module}/{id}/thumbnail"
        oldAccept = self.headers["Accept"]
        self.headers["Accept"] = "application/octet-stream"
        r = self._get(url)
        self.headers["Accept"] = oldAccept
        return r  # r.content

    def updateAttachment(self, *, module: str, id: int, path: str) -> requests.Response:
        """
        Add or update the attachment of a module item, as a base64 encoded XML
        Add or update the attachment of a module item, as a binary stream
        PUT http://.../ria-ws/application/module/{module}/{__id}/attachment
        Untested
        """
        url = f"{self.appURL}/module/{module}/{id}/attachment"
        with open(path, mode="rb") as f:
            file = f.read()
        return self._put(url, data=file)

    def deleteAttachment(self, *, module: str, id: int) -> requests.Response:
        """
        Delete the attachment of a module item
        DELETE http://.../ria-ws/application/module/{module}/{__id}/attachment
        """
        url = f"{self.appURL}/module/{module}/{id}/attachment"
        return self._delete(url)

    #
    # D RESPONSE orgunit
    #
    def getOrgUnits(self, *, module: str) -> requests.Response:
        """
        Get the list of writable orgUnits for a module
        GET http://.../ria-ws/application/module/{module}/orgunit
        Response body definition: orgunit_1_0.xsd
        """
        url = f"{self.appURL}/module/{module}/orgunit"
        return self._get(url)

    #
    # EXPORT aka report -> LATER
    #

    def listReports(self, module: str) -> requests.Response:
        """
        Get a list of available exports / reports for a module
        GET http://.../ria-ws/application/module/{module}/export

        Response body definition: export_1_0.xsd

        The request will return status code 200 (OK) if the request was correct and
        there is at least one export available. If there is no export for the module
        status code 204 (No Content) will be returned.
        """
        return self._get(f"{self.appURL}/module/{module}/export")

    def reportModuleItem(
        self, *, module: str, itemId: int, exportId: int
    ) -> requests.Response:
        """
        Export a single module item via the reporting system
        GET http://.../ria-ws/application/module/{module}/{__id}/export/{id}
        Response header:
            Content-Type: application/octet-stream
            Content-Disposition: attachment;filename={random-file-name}.{export-specific-file-extension}
        """
        oldAccept = self.headers["Accept"]
        self.headers["Accept"] = "application/octet-stream"
        url = f"{self.appURL}/module/{module}/{itemId}/export/{exportId}"
        r = self._get(url)
        self.headers["Accept"] = oldAccept
        return r

    def reportModuleItems(self, *, module: str, id: int, xml: str) -> requests.Response:
        """
        Export multiple module items via the reporting system
        POST http://.../ria-ws/application/module/{module}/export/{id}
        """
        url = f"{self.appURL}/module/{module}/export/{id}"
        return self._post(url, data=xml)

    #
    # NEW NATIVE VOCABULARY MODULE (can also do json)
    #
    # Labels, Node Classes, TermClassLabel, Node, Term, nodeParents, nodeRelations
    # get, add, delete and sometimes update
    #
    def vInfo(self, *, instanceName: str, id: int = None) -> requests.Response:
        """
        Shows the vocabulary instance information for the give vocabulary.
        GET http://.../ria-ws/application/vocabulary/instances/{instanceName}
        GET http://../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{__id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}"
        if id is not None:
            url = url + "/nodes/{id}"
        return self._get(url)

    def vGetNodes(
        self,
        *,
        instanceName: str,
        offset: int = 0,
        limit: int = 100,
        termContent: str = None,
        status: str = None,
        nodeName: str = None,
    ) -> requests.Response:
        """
        The request returns available vocabulary nodes of the vocabulary instance.
        GET http://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/search
        Todo: json response
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/search"
        params: dict[str, Union[int, str]] = {
            "offset": offset,
            "limit": limit,
        }  # dict[str, int, str]
        # for each in termContent, status, nodeName:
        if termContent is not None:
            params["termContent"] = termContent
        if status is not None:
            params["status"] = status
        if nodeName is not None:
            params["nodeName"] = nodeName
        return self._get(url, params=params)
        # r = self.session.get(url, headers=self.headers, auth=self.auth, params=params)

    def vUpdate(self, *, instanceName: str, xml: str) -> requests.Response:
        """
        Update Vocabulary Instance
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}
        Request body definition: instance element from vocabulary_1_1.xsd
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}"
        return self._put(url, data=xml)

    # LABELS
    def vGetLabels(self, *, instanceName: str) -> requests.Response:
        """
        Get Vocabulary Instance labels
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels"
        return self._get(url)

    def vAddLabel(self, *, instanceName: str, xml: str) -> requests.Response:
        """
        Add Vocabulary Instance label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels"
        return self._post(url, data=xml)

    def vDelLabel(self, *, instanceName: str, language: str) -> requests.Response:
        """
        Delete Vocabulary Instance label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels/{language}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels/{language}"
        return self._delete(url)

    # NODE CLASSES
    def vGetNodeClasses(self, *, instanceName: str) -> requests.Response:
        """
        Get Vocabulary Instance Node Classes
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses"
        return self._get(url)

    def vAddNodeClass(self, *, instanceName: str, xml: str) -> requests.Response:
        """
        Add Vocabulary Instance Node Class
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses"
        return self._post(url, data=xml)

    def vAddNodeClassLabel(
        self, *, instanceName: str, className: str, xml: str
    ) -> requests.Response:
        """
        Add Vocabulary Instance Node Class Label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels"
        return self._post(url, data=xml)

    def vDelNodeClassLabel(
        self, *, instanceName: str, className: str, language: str
    ) -> requests.Response:
        """
        Delete Vocabulary Instance Node Class Label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels/{language}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels/{language}"
        return self._delete(url)

    def vDelNodeClass(self, *, instanceName: str, className: str) -> requests.Response:
        """
        Delete Vocabulary Instance Node Class
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}
        """
        url = (
            f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}"
        )
        return self._delete(url)

    # TERM CLASSES
    def vGetTermClasses(self, *, instanceName: str) -> requests.Response:
        """
        Get Vocabulary Instance Term Classes
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses"
        return self._get(url)

    def vAddTermClass(self, *, instanceName: str, xml: str) -> requests.Response:
        """
        Add Vocabulary Instance Term Class
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses"
        return self._post(url, data=xml)

    def vDelTermClass(self, *, instanceName: str, className: str) -> requests.Response:
        """
        Delete Vocabulary Instance Term Class
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}
        """
        url = (
            f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}"
        )
        return self._delete(url, data=xml)

    # TermClassLabel
    def vAddTermClassLabel(
        self, *, instanceName: str, className: str, xml: str
    ) -> requests.Response:
        """
        Add Vocabulary Instance Term Class Label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses/{className}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses/{className}/labels"
        return self._post(url, data=xml)

    def vDelTermClassLabel(
        self, *, instanceName: str, className: str, language: str
    ) -> requests.Response:
        """
        Delete Vocabulary Instance Term Class Label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses/{className}/labels/{language}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses/{className}/labels/{language}"
        return self._delete(url)

    # vocabularyNode
    def vNodeByIdentifier(self, *, instanceName: str, id: int) -> requests.Response:
        """
        Get Vocabulary Node by identifier
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        return self._get(url)

    def vAddNode(self, *, instanceName: str, xml: str) -> requests.Response:
        """
        Add Vocabulary Node
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes"
        return self._post(url, data=xml)

    def vDelNode(self, *, instanceName: str, id: int) -> requests.Response:
        """
        Delete Vocabulary Node
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        return self._delete(url)

    def vUpdateNode(self, *, instanceName: str, id: int, xml: str) -> requests.Response:
        """
        Update Vocabulary Node
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        return self._put(url, data=xml)

    # TERM
    def vAddTerm(
        self, *, instanceName: str, nodeId: int, xml: str
    ) -> requests.Response:
        """
        Add Vocabulary Term
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms"
        return self._post(url, data=xml)

    def vUpdateTerm(
        self, *, instanceName: str, nodeId: str, termId: int, xml: str
    ) -> requests.Response:
        """
        Update Vocabulary Term
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}"
        return self._put(url, data=xml)

    def vDelTerm(
        self, *, instanceName: str, nodeId: int, termId: int
    ) -> requests.Response:
        """
        Delete Vocabulary Term
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}"
        return self._delete(url)

    # NodeParent
    def vNodeParents(self, *, instanceName: str, nodeId: int) -> requests.Response:
        """
        Get Vocabulary Node Parents / Default Node Relations
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/
        (I am assuming the trailing slash is a typo.)
        """
        url = (
            f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents"
        )
        return self._delete(url)

    def vAddNodeParent(
        self, *, instanceName: str, nodeId: int, xml: str
    ) -> requests.Response:
        """
        Add Vocabulary Node Parent / Default Node Relations
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/
        """
        url = (
            f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents"
        )
        return self._post(url, data=xml)

    def vDelNodeParent(
        self, *, instanceName: str, nodeId: int, parentNodeId: int
    ) -> requests.Response:
        """
        Delete Vocabulary Node Parent / Default Node Relations
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{parentNodeId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{parentNodeId}"
        return self._delete(url)

    # nodeRelations
    def vNodeRelations(self, *, instanceName: str, nodeId: int) -> requests.Response:
        """
        Get Vocabulary Node Relations / Advanced Node Relations
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations/
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations"
        return self._get(url)

    def vAddNodeRelation(
        self, instanceName: str, nodeId: int, xml: str
    ) -> requests.Response:
        """
        Add Vocabulary Node Relation / Advanced Node Relations
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations/
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations"
        return self._post(url, data=xml)

    def vDelNodeRelation(
        self, instanceName: str, nodeId: int, relationId: str
    ) -> requests.Response:
        """
        Delete Vocabulary Node Relation / Advanced Node Relations
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{relationId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}parents/{relationId}"
        return self._delete(url)

    #
    # HELPERS
    #

    def ETfromString(self, *, xml: str) -> etree:
        return etree.fromstring(bytes(xml, "UTF-8"))

    def toFile(self, *, xml: str, path: str) -> None:
        with open(path, "w", encoding="UTF-8") as f:
            f.write(xml)

    def completeXML(self, *, fragment: str) -> str:
        """
        Expects a moduleItem as xml string, returns a whole
        document as xml string.
        """

        whole = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
            <modules name="Object">
                <moduleItem>
                    {fragment}
                </moduleItem>
            </modules>
        </application>
        """
        return whole

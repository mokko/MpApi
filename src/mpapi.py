import requests

# import logging
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from lxml import etree  # currently only necessary for getSession
from Search import Search
from Module import Module

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
SEE ALSO: 
    http://docs.zetcom.com/ws
"""


class MpApi:
    def __init__(self, *, baseURL, user, pw):
        self.baseURL = baseURL
        self.appURL = baseURL + "/ria-ws/application"
        self.auth = HTTPBasicAuth(user, pw)
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/xml"
        headers["Accept"] = "application/xml;charset=UTF-8"
        self.headers = headers

    #
    # A SESSION
    #
    def getSessionKey(self):
        """
        GET http://.../ria-ws/application/session
        """
        url = self.appURL + "/session"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()

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
    def getDefinition(self, *, module=None):
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
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    #
    # B.2 SEARCHING
    #
    def runSavedQuery(self, *, __id):
        """
        Run a pre-existing saved search
        POST http://.../ria-ws/application/module/{module}/search/savedQuery/{__id}
        """
        url = f"{self.appURL}/module/{module}/search/savedQuery/{id}"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def search(self, *, xml):
        """
        Perform an ad-hoc search for modules items
        POST http://.../ria-ws/application/module/{module}/search/

        New: We're getting the module from the xml to avoid mistakes from redundancy.
        """
        tree = self.ETfromString(xml=xml)
        module = tree.xpath(
            "/s:application/s:modules/s:module/@name",
            namespaces={"s": "http://www.zetcom.com/ria/ws/module/search"},
        )
        if not module[0]:
            raise TypeError("Unknown module")
        url = f"{self.appURL}/module/{module[0]}/search"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    #
    # B.3 WHOLE MODULE ITEMS
    #
    def getItem(self, *, module, id):
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
        url = f"{self.appURL}/module/{module}/{id}"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def createItem(self, *, module, xml):
        """
        Create new module item or items.
        POST http://.../ria-ws/application/module/{module}

        Is there a return value? I would like to know the id
        """
        url = self.appURL + "/module/" + module
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def updateItem(self, *, module, id, xml):
        """
        Update all fields of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}
        """
        url = f"{self.appURL}/module/{module}/{id}"
        r = requests.put(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def deleteItem(self, *, module, id):
        """
        Delete a module item
        DELETE http://.../ria-ws/application/module/{module}/{__id}
        """
        url = f"{self.appURL}/module/{module}/{id}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    #
    # B.4 FIELDs
    #
    def updateField(self, *, module, id, datafield):
        """
        Update a single field of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}/{datafield}
        
        NB: We dont need a createField method since simple dataFields are always created.
        """
        url = f"{self.appURL}/module/{module}/{id}/{datafield}"
        r = requests.put(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    #
    # B.5 REPEATABLE GROUPS
    #
    def createReference(
        self, *, module, id, repeatableGroup, groupId, reference, xml
    ):
        """
        Add a reference to a reference field within a repeatable group
        POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}
        
        Remember that xml is different during downloads than for uploads.
        Upload xml omitts, for example, formattedValues.
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{groupId}/{reference}"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def createRepeatableGroup(self, *, module, id, repeatableGroup, xml):
        """
        Create repeatable group / reference
        #POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}
        eg. https://<host>/<application>/ria-ws/application/module/Address/29011/AdrContactGrp
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def updateRepeatableGroup(self, *, module, id, referenceId):
        """
        Update all fields of repeatable groups / references
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}"
        r = requests.put(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def updateFieldInGroup(self, *, module, id, referenceId, datafield):
        """
        Update a single data field of a repeatable group / reference
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}/{datafield}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}/{datafield}"
        r = requests.put(url, data=xml, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def deleteRepeatableGroup(self, *, module, id, referenceId):
        """
        Delete a complete repeatable group / reference
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{referenceId}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    def deleteReferenceInGroup(self, *, module, id, groupId, referenceId):
        """
        Delete a reference contained within a repeatable group
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}/{__referenceId}
        """
        url = f"{self.appURL}/module/{module}/{id}/{repeatableGroup}/{groupId}/{reference}/{referenceId}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r

    #
    # C ATTACHMENTs AND THUMBNAILs
    #

    def getAttachment(self, *, module, id):
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

        headers = self.headers  # is this a true copy?
        oldAccept = self.headers["Accept"]
        self.headers["Accept"] = "application/octet-stream"
        print(url)
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        self.headers["Accept"] = oldAccept
        return r

    def saveAttachment(self, *, module, id, path):
        """
        Streaming version of getAttachment that saves attachment directly to disk.

        Expects module (e.g. "Multimedia"), id and path (filename) to save attachment
        to.

        Returns nothing useful. UNTESTED!
        """
        url = f"{self.appURL}/module/{module}/{id}/attachment"

        headers = self.headers  # is this a true copy?
        oldAccept = self.headers["Accept"]
        self.headers["Accept"] = "application/octet-stream"
        r = requests.get(url, stream=True, headers=self.headers, auth=self.auth)
        r.raise_for_status()  # todo: replace with r.raise_for_status()?

        with requests.get(url, stream=True, headers=self.headers, auth=self.auth) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        self.headers["Accept"] = oldAccept

    def getThumbnail(self, *, module, __id):
        """
        Get the thumbnail of a module item attachment
        GET http://.../ria-ws/application/module/{module}/{__id}/thumbnail
        """

    def updateAttachment(self, *, module, __id):
        """
        Add or update the attachment of a module item, as a base64 encoded XML
        Add or update the attachment of a module item, as a binary stream
        PUT http://.../ria-ws/application/module/{module}/{__id}/attachment
        """

    def deleteAttachment(self, *, module, __id):
        """
        Delete the attachment of a module item
        DELETE http://.../ria-ws/application/module/{module}/{__id}/attachment
        """

    #
    # D RESPONSE orgunit
    #
    def getOrgUnits(self, *, module):
        """
        Get the list of writable orgUnits for a module
        GET http://.../ria-ws/application/module/{module}/orgunit
        Response body definition: orgunit_1_0.xsd
        """

    #
    # EXPORT aka report -> LATER
    #

    def listReports(self, module):
        """
        Get a list of available exports / reports for a module
        GET http://.../ria-ws/application/module/{module}/export

        Response body definition: export_1_0.xsd

        The request will return status code 200 (OK) if the request was correct and
        there is at least one export available. If there is no export for the module
        status code 204 (No Content) will be returned.
        """

    def reportModuleItem(self, *, module, itemId, exportId):
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
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        self.headers["Accept"] = oldAccept
        return r

    def reportModuleItems(self, *, module, id):
        """
        Export multiple module items via the reporting system
        POST http://.../ria-ws/application/module/{module}/export/{id}
        """

    #
    # NEW NATIVE VOCABULARY MODULE (can also do json)
    #
    # Labels, Node Classes, TermClassLabel, Node, Term, nodeParents, nodeRelations    
    # get
    # add
    # (update)
    # delete
    def vInfo (self, *, instanceName, id=None): 
        """
        Shows the vocabulary instance information for the give vocabulary.
        GET http://.../ria-ws/application/vocabulary/instances/{instanceName}
        GET http://../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{__id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}"
        if id is not None:
            url = url + "/nodes/{id}"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        r.raise_for_status()
        return r
    
    def vGetNodes (self, *, instanceName, offset=0, limit=100, termContent=None, 
                   status=None, nodeName=None ):
        """
        The request returns available vocabulary nodes of the vocabulary instance.
        GET http://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/search
        Todo: json response
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/search"
        params = {
            "offset": offset,
            "limit": limit
        }
        #for each in termContent, status, nodeName:              
        if termContent is not None:
            params["termContent"] = termContent
        if status is not None:
            params["status"] = status
        if nodeName is not None:
            params["nodeName"] = nodeName
        r = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        return r

    def vUpdate (self, *, instanceName, xml):
        """
        Update Vocabulary Instance
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}
        Request body definition: instance element from vocabulary_1_1.xsd
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}"
        r = requests.put(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    #LABELS
    def vGetLabels (self, *, instanceName):
        """
        Get Vocabulary Instance labels
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        return r
    
    def vAddLabel (self, *, instanceName, xml):
        """
        Add Vocabulary Instance label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelLabel (self, *, instanceName, language):
        """
        Delete Vocabulary Instance label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/labels/{language}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/labels/{language}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r
    
    #NODE CLASSES    
    def vGetNodeClasses (self, *, instanceName):
        """
        Get Vocabulary Instance Node Classes
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        return r

    def vAddNodeClass (self, *, instanceName, xml):
        """
        Add Vocabulary Instance Node Class
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vAddNodeClassLabel (self, *, instanceName, className, xml):
        """
        Add Vocabulary Instance Node Class Label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelNodeClassLabel (self, *, instanceName, className, language):
        """
        Delete Vocabulary Instance Node Class Label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels/{language}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}/labels/{language}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r
        
    def vDelNodeClass (self, *, instanceName, className):
        """
        Delete Vocabulary Instance Node Class
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    #TERM CLASSES
    def vGetTermClasses (self, *, instanceName):
        """
        Get Vocabulary Instance Term Classes
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        return r

    def vAddTermClass (self, *, instanceName, xml):
        """
        Add Vocabulary Instance Term Class
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses        
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelTermClass (self, *, instanceName, className):
        """
        Delete Vocabulary Instance Term Class
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodeClasses/{className}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodeClasses/{className}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    #TermClassLabel
    def vAddTermClassLabel (self, *, instanceName, className, xml):
        """
        Add Vocabulary Instance Term Class Label
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses/{className}/labels
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses/{className}/labels"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelTermClassLabel (self, *, instanceName, className, language):
        """
        Delete Vocabulary Instance Term Class Label
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/termClasses/{className}/labels/{language}    
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/termClasses/{className}/labels/{language}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    #vocabularyNode
    def vNodeByIdentifier(self, *, instanceName, id):
        """
        Get Vocabulary Node by identifier
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        return r

    def vAddNode (self, *, instanceName, xml):
        """
        Add Vocabulary Node
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r
    
    def vDelNode (self, *, instanceName, id):
        """
        Delete Vocabulary Node
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    def vUpdateNode (self, *, instanceName, id, xml):
        """
        Update Vocabulary Node
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{id}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{id}"
        r = requests.put(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    #TERM
    def vAddTerm (self, *, instanceName, nodeId, xml):
        """
        Add Vocabulary Term
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r
    
    def vUpdateTerm (self, *, instanceName, nodeId, termId, xml):
        """
        Update Vocabulary Term
        PUT https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}"
        r = requests.put(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelTerm (self, *, instanceName, nodeId, termId):
        """
        Delete Vocabulary Term
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/terms/{termId}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    #NodeParent
    def vNodeParents (self, instanceName, nodeId):
        """
        Get Vocabulary Node Parents / Default Node Relations
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/        
        (I am assuming the trailing slash is a typo.)
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    def vAddNodeParent (self, instanceName, nodeId, xml):
        """
        Add Vocabulary Node Parent / Default Node Relations
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents"
        r = requests.post(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelNodeParent (self, instanceName, nodeId, parentNodeId):
        """
        Delete Vocabulary Node Parent / Default Node Relations
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{parentNodeId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{parentNodeId}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r

    #nodeRelations
    def vNodeRelations (self, instanceName, nodeId):
        """
        Get Vocabulary Node Relations / Advanced Node Relations
        GET https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations/
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations"
        r = requests.get(url, headers=self.headers, auth=self.auth)
        return r

    def vAddNodeRelation (self, instanceName, nodeId, xml):
        """
        Add Vocabulary Node Relation / Advanced Node Relations
        POST https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations/
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}/relations"
        r = requests.get(url, headers=self.headers, auth=self.auth, data=xml)
        return r

    def vDelNodeRelation (self, instanceName, nodeId, relationId):
        """
        Delete Vocabulary Node Relation / Advanced Node Relations
        DELETE https://.../ria-ws/application/vocabulary/instances/{instanceName}/nodes/{nodeId}/parents/{relationId}
        """
        url = f"{self.appURL}/vocabulary/instances/{instanceName}/nodes/{nodeId}parents/{relationId}"
        r = requests.delete(url, headers=self.headers, auth=self.auth)
        return r
        
    #    
    # HELPERS
    #

    def ETfromString(self, *, xml):
        return etree.fromstring(bytes(xml, "UTF-8")) 

    def toFile(self, *, xml, path):
        with open(path, "w", encoding="UTF-8") as f:
            f.write(xml)


if __name__ == "__main__":
    from pathlib import Path

    with open("../sdata/credentials.py") as f:
        exec(f.read())

    def save(content, path):
        with open(path, "wb") as f:
            f.write(r.content)

    print(f"{baseURL}:{user}:{pw}")
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = api.reportModuleItem(module="Object", itemId="744767", exportId="45003")
    save(r.content, "report45003.xml")
    r = api.reportModuleItem(module="Object", itemId="744767", exportId="48014")
    save(r.content, "report48014.xml")
    r = api.reportModuleItem(module="Object", itemId="744767", exportId="57028")
    save(r.content, "report57028.xml")

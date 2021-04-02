import requests
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
#from lxml import etree # necessary?
from Search import Search
from Module import Module

"""
MpApi - MuseumPlus API Client  

USAGE
    api = MpWebService(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", ID="12345")
    key = api.getSessionKey()
    api.toFile(response=r, path="path/to/file.xml")

Which are the modules our instance knows
    - _SystemMessage
    - _SystemCopyScheme
    - _SystemJob

    - Accessory
    - Address
    - AddressGroup
    - CollectionActivity
    - Conservation
    - Contract
    - Datasource
    - DefDimension
    - DefLiterature
    - Exhibition
    - Event
    - Function
    - FunctionGenerator
    - InventoryNumber
    - Literature
    - Movement
    - Multimedia: DigitalAsset
    - MultimediaGroup
    - Object
    - ObjectGroup: Gruppe
    - Ownership
    - OrganisationUnit
    - Place
    - Parameter
    - Registrar
    - Person
    - Search
    - Task
    - Template
    - User
    - UserGroup
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
        headers["Accept"] = "application/xml"
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

        if r.status_code != 200:
            raise TypeError(f"Request response status code: {r.status_code}")

        tree = etree.fromstring(bytes(r.text, "utf8"))
        key = tree.xpath(
            "/s:application/s:session/s:key/text()",
            namespaces={"s": "http://www.zetcom.com/ria/ws/session"},
        )
        return key


    #
    # B REQUESTS WITH module.xsd response
    # 

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
        if r.status_code != 200:
            print(url)
            print(r.text)
            raise TypeError(f"Request response status code: {r.status_code}")
        return r
    
    #
    # B.2 SEARCHING 
    #
    def runSavedQuery(self, *, __id):
        """
        Run a pre-existing saved search
        POST http://.../ria-ws/application/module/{module}/search/savedQuery/{__id}
        """
        
    def search(self, *, module, xml):
        """
            Perform an ad-hoc search for modules items
            POST http://.../ria-ws/application/module/{module}/search/
        """
        url = self.appURL + "/module/" + module + "/search"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)

        if r.status_code != 200:
            print(url)
            print(r.text)
            raise ValueError(f"Response status code: {r.status_code}")
        return r

    #
    # B.3 WHOLE MODULE ITEMS
    #
    def getItem(self, *, module, __id):
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
        url = self.appURL + "/module/" + module + "/" + __id
        r = requests.get(url, headers=self.headers, auth=self.auth)

        print(r)
        if r.status_code != 200:
            raise ValueError(f"Request response status code: {r.status_code}")
        return r

    def createItem (self, *, module, xml):
        """
        Create new module item or items.
        POST http://.../ria-ws/application/module/{module}
        
        Is there a return value? I would like to know the id
        """
        url = self.appURL + "/module/" + module 
        #xml=etree.tostring(nodes)
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)

        if r.status_code != 200:
            print(url)
            print(r.text)
            raise ValueError(f"Request response status code: {r.status_code}")
        return r

    def updateItem(self, *, module, __id):
        """
        Update all fields of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}
        """
    def deleteItem(self, *, module, __id):
        """
        Delete a module item
        DELETE http://.../ria-ws/application/module/{module}/{__id}
        """
    #
    # B.4 FIELDs
    #
    def updateField(self, *, module, __id, datafield):
        """
        Update a single field of a module item
        PUT http://.../ria-ws/application/module/{module}/{__id}/{datafield}
        """
    #
    # B.5 REPEATABLE GROUPS
    #
    def createRerefence(self, *, module, __id, repeatableGroup, __groupId, reference, xml):
        """
        Add a reference to a reference field within a repeatable group
        POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}
        """

    def createRepeatableGroup(self,*, module, __id, repeatableGroup, xml):
        """
        Create repeatable group / reference 
        #POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}
        """
    def updateRepeatableGroup(self, *, module,__id, __referenceId):
        """
        Update all fields of repeatable groups / references
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """

    def updateFieldInGroup(self, *, module, __id, __referenceId, datafield):
        """
            Update a single data field of a repeatable group / reference
            PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}/{datafield}
        """

    def deleteRepeatableGroup(self,*, module, __id, __referenceId):
        """
        Delete a complete repeatable group / reference
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """
    def deleteReferenceInGroup(self, *, module, __id, __groupId, __referenceId):
        """
        Delete a reference contained within a repeatable group
        DELETE http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}/{__referenceId}    
        """
    #
    # C ATTACHMENTs AND THUMBNAILs
    # 

    def getAttachment(self,*, module, __id):
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
    def reportModuleItem(self, *, module, __id, exportId):
        """
        Export a single module item via the reporting system
        GET http://.../ria-ws/application/module/{module}/{__id}/export/{id}
        Response header:
            Content-Type: application/octet-stream
            Content-Disposition: attachment;filename={random-file-name}.{export-specific-file-extension}
        """
    def reportModuleItems(self, *, module, id):
        """
        Export multiple module items via the reporting system
        POST http://.../ria-ws/application/module/{module}/export/{id}
        """

    #
    # HELPER
    #

    def toFile(self, *, response, path):
        with open(path, "w", encoding='utf8') as f:
            f.write(response.text)


if __name__ == "__main__":
    from pathlib import Path
    with open("credentials.py") as f:
        exec(f.read())

    print(f"{baseURL}:{user}:{pw}")
    api = MpApi(baseURL=baseURL, user=user, pw=pw)

    #project: exhibit objects
    project=Path("../sdata/exhibitObjects")
    s = Search(module="Object")
    s.addCriterion(operator="equalsField", field="Object.ObjRegistrarRef.RegExhibitionRef.__id", value="20222")
    print(s.toString())
    s.validate()
    s.toFile(path=project.join("search.xml"))

    r = api.search(module="Object", et=s.et)
    api.toFile(response=r, path=project.join("response.xml"))

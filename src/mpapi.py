import requests
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

        self.check_request(r)

        tree = self.ETfromString(r.text)

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
        self.check_request(r)
        return r

    #
    # B.2 SEARCHING
    #
    def runSavedQuery(self, *, __id):
        """
        Run a pre-existing saved search
        POST http://.../ria-ws/application/module/{module}/search/savedQuery/{__id}
        """

    def search(self, *, xml):
        """
        Perform an ad-hoc search for modules items
        POST http://.../ria-ws/application/module/{module}/search/

        We'new getting the module from the xml to avoid mistakes from redundancy.
        """
        tree = self.ETfromString(xml=xml)
        module = tree.xpath(
            "/s:application/s:modules/s:module/@name",
            namespaces={"s": "http://www.zetcom.com/ria/ws/module/search"},
        )
        if not module[0]:
            raise TypeError("Unknown module")
        url = self.appURL + "/module/" + module[0] + "/search"
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)
        self.check_request(r)
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
        self.check_request(r)
        return r

    def createItem(self, *, module, xml):
        """
        Create new module item or items.
        POST http://.../ria-ws/application/module/{module}

        Is there a return value? I would like to know the id
        """
        url = self.appURL + "/module/" + module
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)

        self.check_request(r)
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
    def createRerefence(
        self, *, module, __id, repeatableGroup, __groupId, reference, xml
    ):
        """
        Add a reference to a reference field within a repeatable group
        POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup}/{__groupId}/{reference}
        """

    def createRepeatableGroup(self, *, module, __id, repeatableGroup, xml):
        """
        Create repeatable group / reference
        #POST http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}
        """

    def updateRepeatableGroup(self, *, module, __id, __referenceId):
        """
        Update all fields of repeatable groups / references
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}
        """

    def updateFieldInGroup(self, *, module, __id, __referenceId, datafield):
        """
        Update a single data field of a repeatable group / reference
        PUT http://.../ria-ws/application/module/{module}/{__id}/{repeatableGroup|reference}/{__referenceId}/{datafield}
        """

    def deleteRepeatableGroup(self, *, module, __id, __referenceId):
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
        r = requests.get(url, headers=self.headers, auth=self.auth)
        self.check_request(r)
        self.headers["Accept"] = oldAccept
        return r

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
    # HELPERS
    #

    def ETfromString(self, *, xml):
        return etree.fromstring(xml)  # bytes(xml, "UTF-8")

    def toFile(self, *, xml, path):
        with open(path, "w", encoding="UTF-8") as f:
            f.write(xml)

    def check_request(self, r):
        if r.status_code != 200:
            raise TypeError(f"Request response status code: {r.status_code}")


if __name__ == "__main__":
    from pathlib import Path

    with open("../sdata/credentials.py") as f:
        exec(f.read())

    print(f"{baseURL}:{user}:{pw}")
    api = MpApi(baseURL=baseURL, user=user, pw=pw)

    s = Search(module="Object")
    s.addCriterion(
        field="ObjRegistrarRef.RegExhibitionRef.__id",
        operator="equalsField",
        value="20222",
    )
    s.validate(mode="search")
    print("About to do a request")
    api.search(xml=s.toString())

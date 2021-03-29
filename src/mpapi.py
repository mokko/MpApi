import requests
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from lxml import etree
from Search import Search
from ObjectGroup import ObjectGroup

"""
mpApi - MuseumPlus API Client  

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


class mpApi:
    def __init__(self, *, baseURL, user, pw):
        self.baseURL = baseURL
        self.appURL = baseURL + "/ria-ws/application"
        self.auth = HTTPBasicAuth(user, pw)
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/xml"
        headers["Accept"] = "application/xml"
        self.headers = headers

    def getItem(self, *, module, ID):
        url = self.appURL + "/module/" + module + "/" + ID
        r = requests.get(url, headers=self.headers, auth=self.auth)

        print(r)
        if r.status_code != 200:
            raise TypeError(f"Request response status code: {r.status_code}")
        return r

    # GET http://.../ria-ws/application/session
    def getSessionKey(self):  
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

    def getDefinition(self, *, module=None):
        """
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

    # POST http://.../ria-ws/application/module/{module}/search/
    def search(self, *, module, et=None, xml=None):
        url = self.appURL + "/module/" + module + "/search"
        if et is not None:
            xml=etree.tostring(et)
        r = requests.post(url, data=xml, headers=self.headers, auth=self.auth)

        if r.status_code != 200:
            print(url)
            print(r.text)
            raise TypeError(f"Request response status code: {r.status_code}")
        return r

    #
    # Public Helpers
    #

    def toFile(self, *, response, path):
        """Write to file"""
        tree = etree.fromstring(bytes(response.text, "utf8"))
        et = etree.ElementTree(tree)
        et.write(str(path), pretty_print=True)

    def toString(self, *, response):
        """Return response as string"""
        return response.text
        #etree.indent(self.et)
        #return etree.tostring(self.et, pretty_print=True, encoding="unicode")  # not UTF-8
if __name__ == "__main__":
    from pathlib import Path
    with open("credentials.py") as f:
        exec(f.read())

    print(f"{baseURL}:{user}:{pw}")
    api = mpApi(baseURL=baseURL, user=user, pw=pw)

    #project: exhibit objects
    project=Path("../sdata/exhibitObjects")
    s = Search(module="Object")
    s.addCriterion(operator="equalsField", field="Object.ObjRegistrarRef.RegExhibitionRef.__id", value="20222")
    print(s.toString())
    s.validate()
    s.toFile(path=project.join("search.xml"))

    r = api.search(module="Object", et=s.et)
    api.toFile(response=r, path=project.join("response.xml"))

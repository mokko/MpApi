import requests
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from lxml import etree
from Search import Search
from ObjectGroup import ObjectGroup
from wsgiref import validate

"""
mpApi - MuseumPlus API Client  

USAGE
    api = MpWebService(baseURL=baseURL, user=user, pw=pw)
    r = api.getItem(module="Object", ID="12345")
    key = api.getSessionKey()
    api.write(response=r, path="path/to/file.xml")

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
    http://docs.zetcom.com/ws/
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
        returns a request containing module definition for specified module
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
        xml = """<application xmlns="http://www.zetcom.com/ria/ws/module/search" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd">
          <modules>
          <module name="ObjectGroup">
            <search limit="10" offset="0">
              <expert>
                <and>
                  <equalsField fieldPath="__id" operand="29825" />
                </and>
              </expert>
            </search>
          </module>
        </modules>
        </application>"""

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
    # Helpers
    #

    def write(self, *, response, path):
        tree = etree.fromstring(bytes(response.text, "utf8"))
        et = etree.ElementTree(tree)
        et.write(path, pretty_print=True)


if __name__ == "__main__":

    with open("credentials.py") as f:
        exec(f.read())

    print(f"{baseURL}:{user}:{pw}")
    api = mpApi(baseURL=baseURL, user=user, pw=pw)

    s = Search(module="ObjectGroup")
    s.addCriterion(operator="equalsField", field="__id", value="29825")
    s.validate()
    s.write(path="../data/search.xml")
    r = api.search(module="ObjectGroup", et=s.et)
    api.write(response=r, path="../data/objectGroup.xml")
    ogr = ObjectGroup(xml=bytes(r.text, "utf8"))
    for each in ogr.items():
        print(each)
        obj = api.getItem(module="Object", ID=each[0])
        api.write(response=obj, path=f"../data/obj{each[0]}.xml")

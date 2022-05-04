import datetime
from mpapi.search import Search

"""
Set SMBFreigabe for all objects in group with id 117396

First filter for objects in the group that are not yet approved (freigegeben),
then work on the not approved object.
"""


class BoxerAufstand:
    def Input(self):
        r = {
            "3 Wege Boxeraufstand": "117396",
        }
        return r

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def search(self, Id, limit=-1):
        """
        Objects in group with the ID specified in parameter ID
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=Id,  # using voc id
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # use id? Daten freigegeben für SMB-digital
        )
        query.addField(field="ObjPublicationGrp")
        query.addField(field="ObjPublicationGrp.repeatableGroupItem")
        query.addField(field="ObjPublicationGrp.PublicationVoc")
        query.addField(field="ObjPublicationGrp.TypeVoc")
        # query.print()
        return query

    def onItem(self):
        """
        I can't decide if I should run independent jobs for the marker and for
        SMB Freigabe or everything should be in one thing.

        for every identified record, set SMBFreigabe
        """
        return self.setObjectFreigabe  # returns a callback

    def setObjectFreigabe(self, *, itemN, user):
        """
        We're inside Object's nodeItem here
        We have already filtered out cases where SMBFreigabe exists
        """
        # print (node)

        Id = itemN.xpath("@id")[0]
        today = datetime.date.today()
        module = "Object"
        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
              <modules>
                <module name="{module}">
                  <moduleItem id="{Id}">
                    <repeatableGroup name="ObjPublicationGrp">
                        <repeatableGroupItem>
                            <dataField dataType="Date" name="ModifiedDateDat">
                                <value>{today}</value>
                            </dataField>
                            <dataField dataType="Varchar" name="ModifiedByTxt">
                                <value>{user}</value>
                            </dataField>
                           <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                             <vocabularyReferenceItem id="1810139"/>
                           </vocabularyReference>
                           <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                             <vocabularyReferenceItem id="2600647"/>
                           </vocabularyReference>
                       </repeatableGroupItem>
                    </repeatableGroup>
                  </moduleItem>
                </module>
              </modules>
            </application>
        """

        payload = {
            "type": "createRepeatableGroup",
            "module": module,
            "id": Id,
            "repeatableGroup": "ObjPublicationGrp",
            "xml": xml,
            "success": f"{module} {Id}: set object smbfreigabe",
        }

        return payload

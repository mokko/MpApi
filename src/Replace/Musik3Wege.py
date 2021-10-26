from Search import Search
import datetime

"""
Set SMBFreigabe for all objects in group with id 106400
"""


class BoxerAufstand:
    def input(self):
        r = {
            "3Wege Musikinstrumente": "106400",
        }
        return r

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def search(self, id, limit=-1):
        """
        Objects in group 117396
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=id,  # using voc id
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
        I cant decide if I should run independent jobs for the marker and for
        SMB Freigabe or everything should be in one thing.

        for every identified record, set SMBFreigabe
        """
        return self.setObjectFreigabe  # returns a callback

    def setObjectFreigabe(self, *, node, user):
        """
        We're inside Objects's nodeItem here
        We have already filtered out cases where SMBFreigabe exists already
        """
        # print (node)

        id = node.xpath("@id")[0]
        today = datetime.date.today()
        module = "Object"
        xml = f"""
            <application xmlns="http://www.zetcom.com/ria/ws/module">
              <modules>
                <module name="{module}">
                  <moduleItem id="{id}">
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
            "id": id,
            "repeatableGroup": "ObjPublicationGrp",
            "xml": xml,
            "success": f"{module} {id}: set object smbfreigabe",
        }

        return payload

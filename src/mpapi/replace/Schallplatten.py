from Search import Search
import datetime

"""
REMOVE SMBFreigabe for all Schallplatten and CDs in EM-Medienarchiv.

unfinished, untested
"""


class Schallplatten:
    def input(self):
        r = {
            "Schallplatten": "117396",
        }
        return r

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def search(self, id, limit=-1):
        """
        Objects
        - in EM-Medienarchiv that have
        - Sachbegriff Schallplatte ODER CD -> TechnicalTermEthnologicalVoc
        - Freigabe Typ != SMB-Digital
        - Freigabe Freigabe != Ja
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",  #
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd; we're using a modified version of the xsd file
            value="EMMedienarchiv",
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # use id? Daten freigegeben für SMB-digital
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="ObjPublicationVgr",
            value="1810139",  # use id? 1810139: yes
        )
        query.addCriterion(
            operator="equalsField",  #
            field="TechnicalTermEthnologicalVoc",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="4289178",  # Schallplatte:4289178 CD: 4288787
        )
        query.OR()
        query.addCriterion(
            operator="equalsField",  #
            field="TechnicalTermEthnologicalVoc",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="4288787",  # Schallplatte:4289178 CD: 4288787
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
        # 4491690: Nein
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
                             <vocabularyReferenceItem id="4491690"/>
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
            "success": f"{module} {id}: rm object smbfreigabe",
        }

        return payload

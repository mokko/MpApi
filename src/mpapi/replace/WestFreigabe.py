import datetime
from mpapi.search import Search


class WestFreigabe:
    def Input(self):
        STO = {
            # Westflügel, Westspange Eröffnung
            "O1.189.01.K1 M13": "4220560",
            "O2.017.B2 M37": "4220571",
            "O2.019.P3 M39": "4220580",
            "O2.029.B3 M15": "4220589",
            "O2.037.B3 M16": "4220679",
            "O2.124.K1 M14": "4220743",
            "O2.133.K2 M12": "4220744",
            "O2.160.02.B2 SM Afrika": "4220747",
            "O3.014.B2 M61": "4220964",
            "O3.021.B3 M44": "4220994",
            "O3.090.K1 M43StuSamZ-Asien": "4221084",
            "O3.097.K2 M42": "4221123",
            "O3.125.02.B2 M60": "4221168",
            "O3.126.P3 M62": "4221189",
            "O3.127.01.B3 M45": "4221214",
        }
        # return STOs
        # r = {'M39locId': "4220580"} # for testing
        return STO

    def loop(self):
        """
        loop thru objects in the results
        """
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

    def search(self, Id, limit=-1):
        """
        We're trying to find exactly the right records in one go.
        - Objects at a certain locationId
        - Objects that are not SMBfreigegeben yet

        Nicht freigegeben can be expressed in two ways SMBFreigabe = No or no SMBFreigabe
        in any case we leave records alone that have SMBFreigabe already.

        We used to also select VEs. Now we exclude Primärverpackungen.
        """
        query = Search(module="Object", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="ObjCurrentLocationVoc",
            value=Id,  # using voc id
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="ObjPublicationGrp.TypeVoc",
            value="2600647",  # use id? Daten freigegeben für SMB-digital
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="__orgUnit",
            value="AKuPrimarverpackungen",  # 1632806EM-Primärverpackungen
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

    def setObjectFreigabe(self, *, itemN, user):
        """
        We're inside Object's nodeItem here. We've already filtered out cases
        where SMBFreigabe exists, so only cases remain without SMBFreigabe.
        """
        Id = itemN.xpath("@id")[0]
        print("   setting freigabe")
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

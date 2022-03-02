"""
Fotografen:
- look at asset records of the whole AKu 
- only subset that has urheber/fotograf Jürgen Liepe, Jörg von Bruchhausen
- set SMBFreigabe for those assets

__orgUnit

"""

import datetime

from Search import Search


class DigiP:
    def input(self):
        return {"locId": "4220557"}

    def loop(self):
        return "/m:application/m:modules/m:module[@name = 'Multimedia']/m:moduleItem"

    def search(self, Id, limit=-1):
        query = Search(module="Multimedia", limit=limit)
        query.AND()
        query.addCriterion(
            operator="equalsField",
            field="MulObjectRef.ObjCurrentLocationVoc",  # ObjCurrentLocationVoc
            value=Id,  # using voc id
        )
        query.addCriterion(
            operator="equalsField",  # equalsTerm
            field="MulTypeVoc",  # ObjCurrentLocationVoc
            value="4457921",  # using voc id Digitalisat p = 4457921
        )
        query.addCriterion(
            operator="notEqualsField",  # equalsTerm
            field="MulApprovalGrp.TypeVoc",  # ObjCurrentLocationVoc
            value="1816002",  # using vocId SMB-Digital = 1816002
        )
        return query

    def onItem(self):
        return self.setAssetFreigabe  # returns a callback

    def setAssetFreigabe(self, *, itemN, user):
        """
        This is payload. Untested.
        We're inside Multimedia's nodeItem here
        We have already filtered to our hearts delight, so can change
        immediately.
        """
        # print (itemN)

        Id = itemN.xpath("@id")[0]
        today = datetime.date.today()
        module = "Multimedia"
        sort = 1  # unsolved! I suspect it can be None or missing
        xml = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{module}">
              <moduleItem id="{Id}">
                <repeatableGroup name="MulApprovalGrp">
                    <repeatableGroupItem>
                        <dataField dataType="Varchar" name="ModifiedByTxt">
                            <value>{user}</value>
                        </dataField>
                        <dataField dataType="Date" name="ModifiedDateDat">
                            <value>{today}</value>
                        </dataField>
                       <vocabularyReference name="TypeVoc" id="58635" instanceName="MulApprovalTypeVgr">
                         <vocabularyReferenceItem id="1816002"/>
                       </vocabularyReference>
                       <vocabularyReference name="ApprovalVoc" id="58634" instanceName="MulApprovalVgr">
                         <vocabularyReferenceItem id="4160027"/>
                       </vocabularyReference>
                   </repeatableGroupItem>
                </repeatableGroup>
              </moduleItem>
            </module>
          </modules>
        </application>"""

        payload = {
            "type": "createRepeatableGroup",
            "module": module,
            "id": Id,
            "repeatableGroup": "MulApprovalGrp",
            "xml": xml,
            "success": f"{module} {Id}: set asset smbfreigabe",
        }

        return payload

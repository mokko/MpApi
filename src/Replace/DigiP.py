"""
DigiP: 
- look at asset records for HF Objekte
- only subset that has typ="Digitalisat p"
- set SMBFreigabe for those assets

Interface: I am looking for a decent easy-to-implement interface

    query = plugin.search(limit=1)  # returns search object (which enables us 
                                    # select a set of records later). limit parameter is optional
    xpath = plugin.loop()    # returns a string with an xpath expression (which 
                             # will be used to loop thru the right moduleItems)
    onItem = plugin.onItem() # returns a callback to a method which is called 
                             # inside every selected moduleItem. (It's supposed
                             # make a change on the database upstream.)
    the onItem method is also included in the plugin. I like to refer to it as 
    "the payload". But in the code i prefer a more expressive label such as
    setAssetFreigabe.
"""

import os
import sys
import datetime

from Search import Search
from pathlib import Path


class DigiP:
    def loop (self):
        return "/m:application/m:modules/m:module[@name = 'Multimedia']/m:moduleItem" 
    
    def search(self, limit=-1):
        locId = "4220557"
        query = Search(module="Multimedia", limit=limit) 
        query.AND()
        query.addCriterion(
            operator="equalsField", 
            field="MulObjectRef.ObjCurrentLocationVoc", #ObjCurrentLocationVoc
            value=locId, # using voc id
        )
        query.addCriterion(
            operator="equalsField", #equalsTerm 
            field="MulTypeVoc", #ObjCurrentLocationVoc
            value="4457921", # using voc id Digitalisat p = 4457921
        )
        query.addCriterion(
            operator="notEqualsField", #equalsTerm 
            field="MulApprovalGrp.TypeVoc", #ObjCurrentLocationVoc
            value="1816002", # using vocId SMB-Digital = 1816002
        )
        return query 

    def onItem(self):
        return self.setAssetFreigabe # returns a callback

    def setAssetFreigabe(self, *, node, user):
        """
            This is payload. Untested.
            We're inside Multimedia's nodeItem here
            We have already filtered to our hearts delight, so can change 
            immediately.
        """
        #print (node)

        id = node.xpath("@id")[0]
        today = datetime.date.today()
        module = "Multimedia"
        sort = 1 # unsolved! I suspect it can be None or missing
        xml = f"""
        <application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{module}">
              <moduleItem id="{id}">
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
            "id": id,
            "repeatableGroup": "MulApprovalGrp",
            "xml": xml,
            "success": f"{module} {id}: set asset smbfreigabe" 
        }

        return payload 
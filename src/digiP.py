"""
Looking for a decent easy-to-implement interface

DigiP wants to add SMBFreigabe for assets that have
    type="Digitalisat p"

I want to do that only for HF objects. Do I need both
object and asset data? I dont think so. We just make 
a more complicated search: 
-list all assets that are to objects at room X
 and that are in Bereich AKu-Alle Sammlungen

THis is all a bit complicated, so I will just write it one stupid file
and then look for a dryer solution.

"""
credentials = "emem1.py"  # in pwd

import os
import sys
import datetime
import logging

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

from Module import Module
from Search import Search
from Sar import Sar
from MpApi import MpApi
from lxml import etree
from pathlib import Path

NSMAP = {
    "s" : "http://www.zetcom.com/ria/ws/module/search",
    "m" : "http://www.zetcom.com/ria/ws/module",
}


class DigiP:
    def __init__(self, *, locId, onItem): 
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw) # seems we dont really need it
        self.user = user

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format='[%(asctime)s %(message)s]',
            filename="dbchanges.log",
            filemode="a", # append 
            level=logging.INFO
        )

        xml = self.search(locId=locId) # sets self.ET
        self.cycle(onItem=onItem)
        #this is original xml, makes no sense
        #tree = etree.ElementTree(self.ET)
        #self.ET.write('digiP.debug.xml', pretty_print=True) 

    def cycle(self, onItem):
        """
            This version loops thru the moduleItems of Multimedia records and calls onItem
        """
        itemsL = self.ET.xpath(
            "/m:application/m:modules/m:module[@name = 'Multimedia']/m:moduleItem",
            namespaces=NSMAP,
        )

        for itemN in itemsL:
            mulId = itemN.attrib["id"]
            print(f"mulId {mulId}")
            onItem(node=itemN, user=self.user)

    def search (self, locId, limit=-1):
        out_fn="temp.zml.xml"
        if Path(out_fn).exists():
            print (f"Loading response for temp file {out_fn}")
            self.ET = self.sar.ETfromFile(path=out_fn) 
        else: 
            print (f"New search")
       
            s = Search(module="Multimedia", limit=1) #was limit 
            s.AND()
            s.addCriterion(
                operator="equalsField", 
                field="MulObjectRef.ObjCurrentLocationVoc", #ObjCurrentLocationVoc
                value=locId, # using voc id
            )
            s.addCriterion(
                operator="equalsField", #equalsTerm 
                field="MulTypeVoc", #ObjCurrentLocationVoc
                value="4457921", # using voc id Digitalisat p = 4457921
            )
            s.addCriterion(
                operator="notEqualsField", #equalsTerm 
                field="MulApprovalGrp.TypeVoc", #ObjCurrentLocationVoc
                value="1816002", # using vocId SMB-Digital = 1816002
            )
            print(s.toString())

            print ("About to validate search ...", end="")
            s.validate(mode="search")
            print ("ok")
            response = self.sar.search (xml=s.toString()) # replace with self.api?
            #response.raise_for_status() # is built into api.search
            print (f"Writing response to temp file: {out_fn}")
            self.sar.toFile(xml=response.text, path=out_fn) # replace with self.api?
            self.ET = etree.fromstring(bytes(response.text, "UTF-8"))


if __name__ == "__main__":
    #run from sdata directory
    import argparse
    with open(credentials) as f:
        exec(f.read())
    
    def setAssetFreigabe(*, node, user):
        #we're inside Multimedia's nodeItem here
        #we already filtered to our hearts delight, so can change immediately
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
                        <dataField dataType="Date" name="ModifiedDateDat">
                            <value>{today}</value>
                        </dataField>
                        <dataField dataType="Varchar" name="ModifiedByTxt">
                            <value>{user}</value>
                        </dataField>
                        <dataField dataType="Long" name="SortLnu">
                            <value>{sort}</value>
                        </dataField>
                       <vocabularyReference name="TypeVoc" id="62650" instanceName="MulApprovalTypeVgr">
                         <vocabularyReferenceItem id="2600647"/>
                       </vocabularyReference>
                       <vocabularyReference name="ApprovalVoc" id="1816002" instanceName="MulApprovalVgr">
                         <vocabularyReferenceItem id="4160027"/>
                       </vocabularyReference>
                   </repeatableGroupItem>
                </repeatableGroup>
              </moduleItem>
            </module>
          </modules>
        </application>"""
        
        m = Module(xml=xml)
        m.validate()
        #r = self.api.createRepeatableGroup(
        #    module=module, id=id, repeatableGroup="MulApprovalGrp", xml=xml
        #)
        #r.raise_for_status()
        logging.info(f"objId {id}: set smbfreigabe")

    #main
    #4220557 equals HUF general node, was 4220580
    dp = DigiP(locId="4220557", onItem=setAssetFreigabe)
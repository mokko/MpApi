import argparse
import logging
import os
import sys

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

credentials = "credentials.py"  # in pwd    
with open(credentials) as f:
    exec(f.read())
        
from lxml import etree
#from MpApi.Module import Module
#from MpApi.Search import Search
from MpApi.Client import MpApi
#from MpApi.Sar import Sar

"""
Touch Replace Plugin

==Problem==
If a multimedia record is smb approved, but the linked object record is not updated,
recherche.smb doesn't show the multimedia asset. 

In order to show it, we manually update the record (e.g. by adding and deleting a 
space in the object record) which triggers the update of the record with the asset on 
recherche.smb. 

==Workaround==
Obviously, the recherche.smb update mechanism should be cleverer, but until this happens
I suggest a workaround where we automate the manual update using this update script.

==Pseudo-Algorithm==

Let's use the pack zml file with objects and assets that we get from MpApi. Using lxml,
* we loop thru the object moduleItems, 
* identify linked multimedia moduleItems, 
* double check that resouces are smb-approved
* compare lastModified date of object with lastModified of asset
* if the asset's is newer than the object's
* update the object record so it has a newer date

==Scope==
For the time being, we only do this for HF Objects, but in the future we can do it for 
all object records which have a smb approval.

Why touch?
	"touch is a command used to update the access date and/or modification date of a 
	computer file or directory."
	source: https://en.wikipedia.org/wiki/Touch_(command)

Execute me in a dir with a credentials.py file.

"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

class Touch:
    def __init__(self, *, Input, act=False):
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.act = act

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format="[%(asctime)s %(message)s]",
            filename="touch.log",
            filemode="a",  # append
            level=logging.INFO,
        )

        report = {
            "approvedAssets": 0,
            "ObjRecordsNeedingUpdate": 0
        } # one-based numbers

        print (f"About to parse input {Input}")
        ET = etree.parse(str(Input), ETparser)

        objItems = ET.xpath("/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem", 
            namespaces=NSMAP)

        mmItems = ET.xpath("/m:application/m:modules/m:module[@name = 'Multimedia']/m:moduleItem", 
            namespaces=NSMAP)

        report["ObjectModuleItems"] = len (objItems) + 1 
        report["MultimediaModuleItems"] = len (mmItems) + 1 

        for itemN in objItems:
            objId = itemN.xpath("@id")[0]
            objLastModified = itemN.xpath("m:systemField[@name = '__lastModified']/m:value/text()", namespaces=NSMAP)[0]            
            print (f"objId {objId} {objLastModified}")
            mulRefs = itemN.xpath("m:moduleReference[@name = 'ObjMultimediaRef']/m:moduleReferenceItem/@moduleItemId", 
                namespaces=NSMAP)
            
            for mulId in mulRefs:
                #print (f"   ref {mulId}")
                try:
                    mmItem = ET.xpath(f"""/m:application/m:modules/m:module[
                        @name = 'Multimedia']/m:moduleItem[@id = '{mulId}' and 
                        ./m:repeatableGroup[@name ='MulApprovalGrp']
                        /m:repeatableGroupItem/m:vocabularyReference[@name='TypeVoc']/m:vocabularyReferenceItem[@id= '1816002'] and
                        ./m:repeatableGroup[@name ='MulApprovalGrp']
                        /m:repeatableGroupItem/m:vocabularyReference[@name='ApprovalVoc']/m:vocabularyReferenceItem[@id= '4160027']                    
                        ]""", namespaces=NSMAP)[0]
                except: pass
                else:
                    report["approvedAssets"] = report["approvedAssets"] + 1        
                    mmLastModified = mmItem.xpath("m:systemField[@name = '__lastModified']/m:value/text()", namespaces=NSMAP)[0]            
                    #print (f"\tincluded and approved: {mmItem} {mmLastModified}")
                    if mmLastModified > objLastModified:
                        report["ObjRecordsNeedingUpdate"] = report["ObjRecordsNeedingUpdate"] + 1 
                        print ("obj record older than asset: objId {objId}")
        print (report)

    def search(self, Id, limit=-1):
        """
        We're trying to find exactly the right records in one go.
        - Objects at a certain locationId
        - Objects that are not SMBfreigegeben yet
        whether they have marker or not is irrelevant

        Nicht freigegeben can be expressed in two ways SMBFreigabe = No or no SMBFreigabe
        in any case we leave records alone that have SMBFreigabe already.
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
            field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
            value="EMPrimarverpackungen",  # 1632806EM-Primärverpackungen
        )
        query.addCriterion(
            operator="notEqualsField",  # notEqualsTerm
            field="__orgUnit",
            value="AKuPrimarverpackungen",  # 1632806EM-Primärverpackungen
        )
        # query.NOT()
        # query.addCriterion( # doesn't find records without ObjTextOnlineGrp, while "enthält nicht" in the Gui does find empty records
        #    operator="contains",
        #    field="ObjTextOnlineGrp.TextHTMLClb",
        #    value="SM8HF",
        # )
        # query.OR()
        # then we have to download all records and test them manually
        query.addField(field="ObjTextOnlineGrp.repeatableGroupItem")
        query.addField(field="ObjTextOnlineGrp.TextHTMLClb")
        query.addField(field="ObjTextOnlineGrp.TextClb")
        # query.print()
        return query


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update lastModified date of object records if the multimedia's lastModified is newer")
    parser.add_argument(
        "-i", "--input", required=True, help="source pack file from MpApi"
    )
    parser.add_argument(
        "-a",
        "--act",
        help="include action, without it only show what would be changed",
        action="store_true",
    )
    args = parser.parse_args()

    Touch(Input=args.input, act=args.act)

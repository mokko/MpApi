"""
Touch For MpApi

==Problem==
If an asset is smb approved after the linked object, the photo might not be 
visible on recherche.smb. 

In order to show it, we manually update the object record in RIA which usually 
triggers an update of that record on recherche.smb. 

==Workaround==
Obviously, the recherche.smb update mechanism should be cleverer, but until 
this happens I suggest a workaround where we automate the manual update using 
this update script.

==Pseudo-Algorithm==

Let's begin with the pack zml file with objects and assets that we get from MpApi. 

pack cache
* we loop thru the object moduleItems, 
* identify linked multimedia moduleItems, 
* check that resouces are smb-approved
* compare object's lastModified with asset's lastModified
* if the asset is newer than the object
* update the object record so it has a newer date
live
* if online lastMod is still the save as in cache

==Scope==
For the time being, we only do this for HF Objects, but in the future we could 
apply the same process on other object records which have a smb approval.

Why touch?
	"touch is a command used to update the access date and/or modification date of a 
	computer file or directory."
	source: https://en.wikipedia.org/wiki/Touch_(command)

Execute me in a dir with a credentials.py file.

"""

from datetime import datetime
import dateutil.parser
import logging
from lxml import etree  # type: ignore
from mpapi.client import MpApi
from mpapi.module import Module
from mpapi.search import Search
import os
import sys

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Touch:
    def __init__(self, *, act: bool = False, baseURL: str, user: str, pw: str) -> None:
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.act = act
        print(f"act = {act}")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format="[%(asctime)s %(message)s]",
            filename="touch.log",
            filemode="a",  # append
            level=logging.INFO,
        )

    def pack(self, *, Input: str) -> None:
        report = {
            "approvedAssets": 0,
            "ObjRecordsNeedingUpdate": 0,
        }  # one-based numbers

        print(f"about to parse input {Input}")

        m = Module(file=Input)

        report["ObjectModuleItems"] = m.actualSize(module="Object")
        report["MultimediaModuleItems"] = m.actualSize(module="Multimedia")

        for itemN in m.iter(module="Object"):
            objId = itemN.xpath("@id")[0]
            objLastModified = itemN.xpath(
                "m:systemField[@name = '__lastModified']/m:value/text()",
                namespaces=NSMAP,
            )[0]
            # print(f"objId {objId}")  # {objLastModified}
            mulRefs = itemN.xpath(
                "m:moduleReference[@name = 'ObjMultimediaRef']/m:moduleReferenceItem/@moduleItemId",
                namespaces=NSMAP,
            )

            ET = m.toET()
            for mulId in mulRefs:
                # print (f"   ref {mulId}")
                try:
                    mmItem = ET.xpath(  # type: ignore
                        f"""/m:application/m:modules/m:module[
                        @name = 'Multimedia']/m:moduleItem[@id = '{mulId}' and 
                        ./m:repeatableGroup[@name ='MulApprovalGrp']
                        /m:repeatableGroupItem/m:vocabularyReference[@name='TypeVoc']/m:vocabularyReferenceItem[@id= '1816002'] and
                        ./m:repeatableGroup[@name ='MulApprovalGrp']
                        /m:repeatableGroupItem/m:vocabularyReference[@name='ApprovalVoc']/m:vocabularyReferenceItem[@id= '4160027']                    
                        ]""",
                        namespaces=NSMAP,
                    )[0]
                except:  # it's not an error to have no relatives
                    pass
                else:
                    report["approvedAssets"] = report["approvedAssets"] + 1
                    mmLastModified = mmItem.xpath(
                        "m:systemField[@name = '__lastModified']/m:value/text()",
                        namespaces=NSMAP,
                    )[0]
                    # print (f"\tincluded and approved: {mmItem} {mmLastModified}")
                    if mmLastModified > objLastModified:
                        report["ObjRecordsNeedingUpdate"] = (
                            report["ObjRecordsNeedingUpdate"] + 1
                        )
                        print(
                            f"objId {objId} Object in cache older than asset in cache"
                        )
                        self.touch(objId=objId, lastMod=objLastModified)
                        break  # only one touch per object
        print(report)

    def touch(self, *, objId: int, lastMod: str) -> None:
        # dont rely on a cache file as it might be too old
        q = Search(module="Object")
        q.addCriterion(operator="equalsField", field="__id", value=str(objId))
        q.addField(field="ObjTechnicalTermClb")
        q.addField(field="__lastModified")
        q.validate(mode="search")
        m = self.api.search2(query=q)
        item = m["Object", objId]  # type: ignore

        lastModNew = item.xpath(
            "m:systemField[@name = '__lastModified']/m:value/text()",
            namespaces=NSMAP,
        )[0]
        try:
            sachbegriff = item.xpath(
                "m:dataField[@name = 'ObjTechnicalTermClb']/m:value/text()",
                namespaces=NSMAP,
            )[0]
        except:
            sachbegriff = None
        """
        <dataField dataType="Clob" name="ObjTechnicalTermClb">
          <value>Oboe</value>
        </dataField>
        """
        if sachbegriff is None:  # can I upload None? Probably not...
            print("WARN: sachbegriff is none")
        else:
            if lastMod == lastModNew:
                print(" record not changed since the cache was made, would try writing")
                if self.act is True:
                    self.api.updateField2(
                        mtype="Object",
                        ID=objId,
                        dataField="ObjTechnicalTermClb",
                        value=sachbegriff,
                    )
            # else: lastMod has changed, so somebody already changed the record

    # not at all dry
    def single(self, *, objId: int) -> None:
        q = Search(module="Object")
        q.addCriterion(operator="equalsField", field="__id", value=str(objId))
        q.addField(field="ObjTechnicalTermClb")
        q.addField(field="__lastModified")
        q.validate(mode="search")
        m = self.api.search2(query=q)
        item = m["Object", objId]  # type: ignore

        lastModNew = item.xpath(
            "m:systemField[@name = '__lastModified']/m:value/text()",
            namespaces=NSMAP,
        )[0]
        try:
            sachbegriff = item.xpath(
                "m:dataField[@name = 'ObjTechnicalTermClb']/m:value/text()",
                namespaces=NSMAP,
            )[0]
        except:
            sachbegriff = None
        """
        <dataField dataType="Clob" name="ObjTechnicalTermClb">
          <value>Oboe</value>
        </dataField>
        """
        if sachbegriff is None:  # can I upload None? Probably not...
            print("WARN: sachbegriff is none")
        else:
            print(f" sachbegriff {sachbegriff}")
            if self.act is True:
                self.api.updateField2(
                    mtype="Object",
                    ID=objId,
                    dataField="ObjTechnicalTermClb",
                    value=sachbegriff,
                )
            else:
                print(" would try to touch if in acting mode")


if __name__ == "__main__":
    import argparse

    credentials = "emem1.py"  # in pwd
    credentials = "credentials.py"  # in pwd
    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(
        description="""Update lastModified date of object records if the 
        multimedia's has smb approval and its lastModified is newer"""
    )
    parser.add_argument(
        "-i", "--input", required=False, help="source pack file from MpApi"
    )
    parser.add_argument(
        "-s", "--single", required=False, help="objID for single record"
    )

    parser.add_argument(
        "-a",
        "--act",
        help="include action, without it only show what would be changed",
        action="store_true",
    )
    args = parser.parse_args()
    t = Touch(act=args.act, baseURL=baseURL, pw=pw, user=user)  # type: ignore
    if args.input is not None:
        t.pack(Input=args.input)
    elif args.single is not None:
        t.single(objId=args.single)

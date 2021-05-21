"""
- For an exhibit or a group, get the objects in that set. 
- walk thru the moduleItems
- test for smbfreigabe. If no entry on smbfreigabe, set it

smbfreigabe.py --type exhib --id 20222
"""

import argparse
from lxml import etree
from pathlib import Path
import sys
adir = Path(__file__).parent
sys.path.append(str(adir))  # what the heck?
from Sar import Sar

apath="freigabe-temp.xml"
nsmap={"m": "http://www.zetcom.com/ria/ws/module"}

class Freigabe:
    def __init__(self, *, id, type):
        sar = Sar(baseURL=baseURL, user=user, pw=pw)
        print (f"Getting objects for {type} {id}")
        if Path(apath).exists():
            print ("File exists")
            ET = sar.ETfromFile(path=apath)
        else:
            r = sar.getObjectSet(type=type, id=id)
            sar.toFile(xml=r.text, path=apath)
            ET = etree.fromstring(bytes(r.text, "UTF-8"))
            
        itemsL = ET.xpath(
            "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem",
            namespaces=nsmap,
        )
        for itemN in itemsL:
            objId = itemN.attrib["id"]
            print(objId)

            try: 
                itemN.xpath("""m:repeatableGroup[
                @name='ObjPublicationGrp']/m:repeatableGroupItem/m:vocabularyReference[
                @name="TypeVoc"]/m:vocabularyReferenceItem[
                @id='2600647']""", namespaces=nsmap,
            )[0]
            except:
                print("no smbfreigabe yet")    
                sar._smbfreigabe(id=objId, sort=1)
            else:
                print("already has smbfreigabe")    
    
if __name__ == "__main__":
    with open("../sdata/vierteInstanz.py") as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="smbfreigabe for exhibit or group")
    parser.add_argument("-t", "--type", help="exhibit or group", required=True)
    parser.add_argument("-i", "--id", help="id", required=True)
    args = parser.parse_args()
    
    f = Freigabe(id=args.id, type=args.type)
    
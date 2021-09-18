from pathlib import Path
from Search import Search
from lxml import etree

class Cycle: 
    def perLocId (self, *, locId, limit=-1):
        """
        cycles thru the Object records at id, where id identifies a term in genLocationVgr
        which signifies a location.

        This cycle works onlineBeschreibung ([SM8HF]) and SMB-Freigabe.
        Search for a aktueller standort using id from genlocationVgr 
        
        In lazy mode, suppress a new http search request and work with temp file cache.
        Lazy mode can lead to duplicate changes in the db, so CAUTION advised.
        """
        
        out_fn = f"loc{locId}.xml" # STOid
        needle = "[SM8HF]"
        
       
        if self.lazy is True and Path(out_fn).exists():
            print (f"Loading response for locId {locId} from file")
            ET = self.sar.ETfromFile(path=out_fn) 
        else: 
            print (f"New search for STOid {locId}")
            rXML = self._locSearch(locId=locId, limit=limit)
            self.sar.toFile(xml=rXML, path=out_fn) # temp file for debugging
            ET = etree.fromstring(bytes(rXML, "UTF-8"))
        
        itemsL = ET.xpath(
            "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem",
            namespaces=self.NSMAP,
        )

        for itemN in itemsL:
            objId = itemN.attrib["id"]
            print(objId)
            self.checkOnlineDescription(id=objId,node=itemN, marker=needle)
            self.checkFreigabe(id=objId,node=itemN)

    def _locSearch (self, *, locId, limit=-1):
        """
            make a new search, execute it and return results that list all Object
            records in one location as xml.
        """
        s = Search(module="Object", limit=limit) #Dont forget limits!
        #experiment with fields
        #s.addField(field="__id")
        #s.addField(field="ObjCurrentLocationVoc")
        #s.addField(field="ObjTextOnlineGrp")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb.ValueTxt")
        s.addCriterion(
            operator="equalsField", 
            field="ObjCurrentLocationVoc",
            value=locId, # using voc id
        )
        #s.print()
        s.validate(mode="search")
        r = self.sar.search (xml=s.toString())
        print (r)
        return r.text

"""
How do we define the set of records?

cyclethroughtherecords
testifonlineBeschreibungisfilledin
appendstring"[HumboldtForum]"orcreatenew"[HumboldtForum]"
upload


OG2: Modul36, 37,39,15,16,13(Modul11bleibtzu,Modul12und14sindjeweilsdieGalerienderKuben)
OG3: Modul60, 61,62,44,45,42(Modul43bleibtzu)

O1.189.01.K1 M13: 4220560
O2.017.B2 M37: 4220571
O2.019.P3 M39: 4220580
O2.029.B3 M15: 4220589
O2.037.B3 M16: 4220679
O2.124.K1 M14: 4220743
O2.133.K2 M12: 4220744
O2.160.02.B2 SM Afrika: 4220747
O3.014.B2 M61: 4220964
O3.021.B3 M44: 4220994
O3.090.K1 M43StuSamZ-Asien: 4221084
O3.097.K2 M42: 4221123
O3.125.02.B2 M60: 4221168
O3.126.P3 M62: 4221189
O3.127.01.B3 M45: 4221214

"""
import sys
import os
from lxml import etree

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

from Search import Search
from Sar import Sar

credentials = "credentials.py"  # expect credentials in pwd

NSMAP={
    "s" : "http://www.zetcom.com/ria/ws/module/search",
    "m" : "http://www.zetcom.com/ria/ws/module",
}

class Replace:
    def __init__(self, *, baseURL, user, pw):
        out_fn = "results.xml"
        sar = Sar(baseURL=baseURL, user=user, pw=pw)
        s = Search(module="Object", limit=10)
        #s.addField(field="__id")
        #s.addField(field="ObjCurrentLocationVoc")
        #s.addField(field="ObjTextOnlineGrp")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb")
        #s.addField(field="ObjTextOnlineGrp.repeatableGroupItem.TextHTMLClb.ValueTxt")
        s.addCriterion(
            operator="equalsField", 
            field="ObjCurrentLocationVoc",
            value="4220580", # using voc id
        )
        s.print()
        s.validate(mode="search")
        r = sar.search (xml=s.toString())
        print (r)
        sar.toFile(xml=r.text, path=out_fn)


if __name__ == "__main__":
    import argparse
    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Command line frontend for Replace.py")
    #parser.add_argument("-j","--job",help="jobtorun",required=True)
    #parser.add_argument("-c","--conf",help="configfile",default="jobs.dsl")
    args = parser.parse_args()

    m = Replace(baseURL=baseURL, pw=pw, user=user)


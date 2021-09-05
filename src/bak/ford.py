import argparse
import os
import re
import sys
from pathlib import Path

adir = Path(__file__).parent
sys.path.append(str(adir))  # what the heck?
# from Saxon import Saxon
# from lvlup.Npx2csv import Npx2csv
from Sar import Sar

saxon_path = "C:\m3\SaxonHE10-5J\saxon-he-10.5.jar"
zpx2mpx = "C:\m3\zpx2npx\zpx2npx.xsl"

with open("C:/m3/MpApi/sdata/vierteInstanz.py") as f:
    exec(f.read())


class Ford:
    def __init__(self):
        # HFObjekte-20210521-zpx.xml
        label = str(Path(".").resolve().parent.name)
        date = str(Path(".").resolve().name)
        out_fn = Path(f"..\..\{label}{date}.xml")
        sar = Sar(baseURL=baseURL, user=user, pw=pw)

        xmlL = list()
        for file in Path().glob("*-clean-*.xml"):
            print(file)
            xmlL.append(sar.xmlFromFile(path=file))
        xml = sar.join(inL=xmlL)
        sar.toFile(xml=xml, path=str(out_fn))

    def old(self):
        # e.g. Afrika-Ausstellung-clean-exhibit20226.xml
        for file in Path().glob("*-clean-*.xml"):
            label = re.match("(.*)-clean-", str(file)).group(1)
            s = Saxon(saxon_path)
            npx_fn = f"2-SHF/{label}-clean.npx.xml"
            s.transform(file, zpx2mpx, npx_fn)
            # print ("About to write csv...")
            Npx2csv(npx_fn, f"2-SHF/{label}")


if __name__ == "__main__":
    Ford()

"""
For a given zpx file, prepare statistics
 
USAGE
    stats.py -i HFobjekte20210523.xml

Number of Object records

No HF Location

pushd \\pk.de\smb\Mediadaten\Projekte\EM\HF-Export

"""
import argparse
from pathlib import Path
import sys
#adir = Path(__file__).parent
#sys.path.append(str(adir))  # what the heck?
sys.path.append("C:/m3/Pipeline/src")
from Saxon import Saxon
saxon_path = "C:\m3\SaxonHE10-5J\saxon-he-10.5.jar"
stat_xsl = "C:/m3/Pipeline/xsl/stat_zpx.xsl"
class Stat:
    def __init__(self, *, input):
        s = Saxon(saxon_path)
        s.transform(input, stat_xsl, "stat.xml")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="display simple stats on zpx file")
    parser.add_argument("-i", "--input", help="zpx file that needs stat", required=True)
    args = parser.parse_args()

    s = Stat(input=args.input)

# -*- coding: utf-8 -*-
"""
How do we define the set of records?

1. cycle through the records
2. test if onlineBeschreibung is filled in
3. append string"[HumboldtForum]" or create new"[HumboldtForum]"
4. upload

OG2: Modul36, 37,39,15,16,13(Modul11bleibtzu,Modul12und14sindjeweilsdieGalerienderKuben)
OG3: Modul60, 61,62,44,45,42(Modul43bleibtzu)

MP.CLIENT
MP.REPLACE
base: basic prg logic
cycle: cycle thru sets of records
checkCondition: for each rec check a condition
act: change records

just taking some notes on how dsl could look like
    HFOpening:
        cycle: perLocId (for multiple ids)
        check  
            checkOnlineDescription, marker="[SM8HF]"
                createOnlineDescription
                updateOnlineDescription
            checkFreigabe
                setFreigabe
"""

import logging
import os
from pathlib import Path
import sys

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

from Sar import Sar
from MpApi import MpApi
from Replace.Cycle import Cycle
from Replace.Check import Check
from Replace.Act import Act

credentials = "credentials.py"  # in pwd
#credentials = "vierteInstanz.py" 
credentials = "emem1.py"  # in pwd


class Replace (Cycle, Check, Act):
    def __init__(self, *, baseURL, user, pw, lazy=False, act=False):
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.lazy = lazy
        self.act = act
        self.user = user # for _smbfreigabe
        self.NSMAP = {
            "s" : "http://www.zetcom.com/ria/ws/module/search",
            "m" : "http://www.zetcom.com/ria/ws/module",
        }

        print (f"LAZY: {self.lazy}")
        print (f"ACT: {self.act}")

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format='%(asctime)s %(message)s',
            filename="dbchanges.log",
            filemode="a",  # append 
            level=logging.INFO
        )

if __name__ == "__main__":
    import argparse
    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Command line frontend for Replace.py")
    parser.add_argument("-l","--lazy", help="lazy modes reads search results from a file cache, for debugging", action='store_true')
    parser.add_argument("-a","--act", help="without act, only show what would be changed, don't actually change the db", action='store_true')
    args = parser.parse_args()

    STOs = {
        #Westflügel, Westspange Eröffnung
        "O1.189.01.K1 M13": 4220560,
        "O2.017.B2 M37": 4220571,
        "O2.019.P3 M39": 4220580,
        "O2.029.B3 M15": 4220589,
        "O2.037.B3 M16": 4220679,
        "O2.124.K1 M14": 4220743,
        "O2.133.K2 M12": 4220744,
        "O2.160.02.B2 SM Afrika": 4220747,
        "O3.014.B2 M61": 4220964,
        "O3.021.B3 M44": 4220994,
        "O3.090.K1 M43StuSamZ-Asien": 4221084,
        "O3.097.K2 M42": 4221123,
        "O3.125.02.B2 M60": 4221168,
        "O3.126.P3 M62": 4221189,
        "O3.127.01.B3 M45": 4221214,
    }

    print ("baseURL: " + baseURL)
    replacer = Replace(baseURL=baseURL, pw=pw, user=user, lazy=args.lazy, act=args.act)
    #replacer.perLocId (locId="4220580") 
    for room in STOs:
        replacer.perLocId(locId=str(STOs[room]))


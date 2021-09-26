"""
SEARCH/REPLACE TOOL for RIA. 
I am still looking for an intermdiary, but a decent and easy-to-implement 
interface for the short-term future.

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

"""

import logging
import os
from pathlib import Path
from lxml import etree
import sys
import importlib

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

from Sar import Sar
from MpApi import MpApi
from Module import Module

credentials = "credentials.py"  # in pwd
#credentials = "vierteInstanz.py" 
credentials = "emem1.py"  # in pwd

NSMAP = {
    "s" : "http://www.zetcom.com/ria/ws/module/search",
    "m" : "http://www.zetcom.com/ria/ws/module",
}

class Replace:
    def __init__(self, *, baseURL, user, pw, lazy=False, act=False):
        print ("baseURL: " + baseURL)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.act = act
        self.lazy = lazy
        self.user = user # for _smbfreigabe

        print (f"ACT: {self.act}")
        print (f"LAZY: {self.lazy}")

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format='[%(asctime)s %(message)s]',
            filename="dbchanges.log",
            filemode="a", # append 
            level=logging.INFO
        )

    def job(self, *, plugin):
        """
            Load a job/plugin by name. Returns the plugin object
        """
        print (f"Loading plugin {plugin}")
        name = "Replace." + plugin
        mod = importlib.import_module(name)
        Plugin = getattr(mod, plugin) 
        return Plugin() # new / constructor?

    def loop(self, *, xpath, onItem):
        """
            Generic loop
        """
        itemsL = self.ET.xpath(xpath, namespaces=NSMAP)

        for itemN in itemsL:
            mulId = itemN.attrib["id"]
            print(f"mulId {mulId}") # not generic yet
            yield onItem(node=itemN, user=self.user) # how generic is that?

    def runPlugin (self, *, plugin, limit=-1):
        """    
            should probably go into the class
        """
        query = plugin.search(limit=limit)  # plugin returns the search object
        replacer.search(query=query)  # save result in self.ET and write to disk for debugging
        xpath = plugin.loop()    # plugin provides xpath for the loop
        onItem = plugin.onItem() # callback for onItem also comes from plugin. 
        for payload in replacer.loop(xpath=xpath, onItem=onItem):
            if args.act is True:
                print (f"ABOUT TO ACT {payload['xml']}")
                m = Module(xml=payload["xml"])
                m.validate()
                if payload["type"] == "createRepeatableGroup":
                    r = self.api.createRepeatableGroup(
                        module=payload["module"], id=payload["id"], repeatableGroup=payload["repeatableGroup"], xml=payload["xml"]
                    )
                    r.raise_for_status()
                    logging.info(payload["success"])

    def search(self, *, query):
        out_fn="temp.zml.xml"
        if self.lazy is True and Path(out_fn).exists():
            print (f"Loading response for temp file {out_fn}")
            self.ET = self.sar.ETfromFile(path=out_fn) 
        else: 
            print (f"New search")
            print (query.toString())
            print ("About to validate search ...", end="")
            query.validate(mode="search")
            print ("ok")
            response = self.sar.search (xml=query.toString()) # replace with self.api?
            #response.raise_for_status() # is built into api.search
            print (f"Writing response to temp file: {out_fn}")
            self.sar.toFile(xml=response.text, path=out_fn) # replace with self.api?
            self.ET = etree.fromstring(bytes(response.text, "UTF-8"))

if __name__ == "__main__":
    import argparse
    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Command line frontend for Replace.py")
    parser.add_argument("-l","--lazy", help="lazy modes reads search results from a file cache, for debugging", action='store_true')
    parser.add_argument("-a","--act", help="include action, without it only show what would be changed", action='store_true')
    parser.add_argument("-j","--job", help="load a plugin and use that code", required=True)

    args = parser.parse_args()

    replacer = Replace(baseURL=baseURL, pw=pw, user=user, lazy=args.lazy, act=args.act)
    plugin = replacer.job(plugin=args.job)
    replacer.runPlugin(plugin=plugin, limit=1) # limit is optional

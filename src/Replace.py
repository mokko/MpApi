"""
SEARCH/REPLACE TOOL for RIA. 
I am still looking for an intermdiary, but a decent and easy-to-implement 
interface for the short-term future.

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
from Search import Search

credentials = "credentials.py"  # in pwd
# credentials = "vierteInstanz.py"
credentials = "emem1.py"  # in pwd

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Replace:
    def __init__(self, *, baseURL, user, pw, lazy=False, act=False):
        print("baseURL: " + baseURL)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.act = act
        self.lazy = lazy
        self.user = user  # for _smbfreigabe

        print(f"ACT: {self.act}")
        print(f"LAZY: {self.lazy}")

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            format="[%(asctime)s %(message)s]",
            filename="dbchanges.log",
            filemode="a",  # append
            level=logging.INFO,
        )

    def job(self, *, plugin):
        """
        Load a job/plugin by name. Returns the plugin object
        """
        print(f"Loading plugin {plugin}")
        name = "Replace." + plugin
        mod = importlib.import_module(name)
        Plugin = getattr(mod, plugin)
        return Plugin()  # new / constructor?

    def loop(self, *, xpath, onItem, type):
        """
        Generic loop
        """
        itemsL = self.ET.xpath(xpath, namespaces=NSMAP)

        for itemN in itemsL:
            Id = itemN.attrib["id"]
            print(f"{type} {Id}")  
            count = itemN.xpath("count(//m:moduleItem)", namespaces=NSMAP)
            #print (f"SYD: {count} inside replace; should be 1")
            yield onItem(itemN=itemN, user=self.user)  

    def runPlugin(self, *, plugin, limit=-1):
        """
        should probably go into the class
        """
        input = plugin.input()
        limit = int(limit)
        count = int(0)
        for key in input:
            print(f"INPUT {key}")
            query = plugin.search(Id=input[key])
            query.validate(mode="search")
            # should validate the query inside replacer? Probably yes
            replacer.search(query=query, id=input[key])
            xpath = plugin.loop()
            moduleType = xpath.split("'")[1] # not particularly generic
            #print (f"T{moduleType}")
            onItem = plugin.onItem()
            for payload in replacer.loop(xpath=xpath, onItem=onItem, type=moduleType):
                # print (f"WOULD ACT {payload['xml']}")
                # it's possible that payload is empty, but it has to exist
                if "xml" in payload:  
                    m = Module(xml=payload["xml"])
                    m.validate()
                    count += 1
                    if args.act is True:
                        if payload["type"] == "createRepeatableGroup":
                            r = self.api.createRepeatableGroup(
                                module=payload["module"],
                                id=payload["id"],
                                repeatableGroup=payload["repeatableGroup"],
                                xml=payload["xml"],
                            )
                        elif payload["type"] == "updateRepeatableGroup":
                            r = self.api.updateRepeatableGroup(
                                module=payload["module"],
                                id=payload["id"],
                                repeatableGroup=payload["repeatableGroup"],
                                xml=payload["xml"],
                                referenceId=refId,
                            )
                        else:
                            raise TypeError("UNKNOWN PAYLOAD TYPE")
                        r.raise_for_status()
                        print(payload["success"])
                        logging.info(payload["success"])
                    if limit != -1 and count >= limit:
                        print(f"Limit of {limit} reached, aborting")
                        return  # break for loop
        print(f"count: {count}")

    def search(self, *, query, id):
        out_fn = f"temp{id}.zml.xml"
        if self.lazy is True and Path(out_fn).exists():
            print(f"Loading response for temp file {out_fn}")
            self.ET = self.sar.ETfromFile(path=out_fn)
        else:
            # print (f"New search")
            # print (query.toString())
            # print ("About to validate search ...", end="")
            query.validate(mode="search")
            # print ("ok")
            response = self.sar.search(xml=query.toString())  # replace with self.api?
            # response.raise_for_status() # is built into api.search
            print(f" writing response to temp file: {out_fn}")
            self.sar.toFile(xml=response.text, path=out_fn)  # replace with self.api?
            self.ET = etree.fromstring(bytes(response.text, "UTF-8"))


if __name__ == "__main__":
    import argparse

    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Command line frontend for Replace.py")
    parser.add_argument(
        "-l",
        "--lazy",
        help="lazy modes reads search results from a file cache, for debugging",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--act",
        help="include action, without it only show what would be changed",
        action="store_true",
    )
    parser.add_argument(
        "-j", "--job", help="load a plugin and use that code", required=True
    )
    parser.add_argument(
        "-L", "--Limit", help="set limit for initial search", default="-1"
    )

    args = parser.parse_args()

    replacer = Replace(baseURL=baseURL, pw=pw, user=user, lazy=args.lazy, act=args.act)
    plugin = replacer.job(plugin=args.job)
    replacer.runPlugin(plugin=plugin, limit=args.Limit)  # set to -1 for production

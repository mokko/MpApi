"""
A search and replace tool for RIA.

Define your search/replace routine in a plugin and run it from the command line

Command Line Usage
    MPreplace -j bla # runs Plugin mpapi.replace.bla

Replace object basically runs
    r = Replace(baseURL=baseURL, user=U, pw=pw) 
    plugin = r.job (plugin=bla)
    r.runPlugin(plugin=plugin)

INTERFACE OF THE PLUGIN
requires a class with four methods 
(1)
'Input' is expected to return a dict with ids and short textual descriptions
    def Input(self):
        return {"3 Wege Boxeraufstand": "117396",}

(2)
'loop' returns an xpath expression which records in the results are processed, 
typically:  
    def loop(self):
        return "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem"

(3)
'search' returns a search query (object).
    def search(self, Id, limit=-1):
        query = Search(module="Object", limit=limit)
        query.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=Id,  
        )
        return query
(4)
'onItem' returns a callback
    def onItem(self):
        return self.setObjectFreigabe  # returns a callback

PSEUDO-ALGORITHM
For every id in the (1) Input dictionary, query the db using the pattern from
(3) search. Get the results looping through them using the (2) xpath 
expression. On every moduleItem, apply (4, 5) onItem(node=node, 
user=user).

"""

import logging
from pathlib import Path
from lxml import etree # type: ignore
import importlib

from mpapi.sar import Sar
from mpapi.client import MpApi
from mpapi.module import Module
from mpapi.search import Search
from typing import Any, Callable, Iterable
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Replace:
    def __init__(self, *, baseURL: str, user: str, pw: str, lazy: bool = False, act: bool = False) -> None:
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

    def job(self, *, plugin:str): 
        """
        Load a job plugin by name. Returns the plugin object
        
        Expects
        * plugin: abbreviated plugin name as str
        """
        print(f"Loading plugin {plugin}")
        name = "mpapi.replace." + plugin
        mod = importlib.import_module(name)
        Plugin = getattr(mod, plugin)
        return Plugin() # what type is plugin?

    def loop(self, *, xpath:str, onItem:Callable, mtype: str) -> Iterable:
        """
        Generic loop
        
        Expects
        * xpath expression that returns a set of moduleItems
        * onItem callable
        * mtype: module type
        """
        itemsL = self.ET.xpath(xpath, namespaces=NSMAP) # type: ignore

        for itemN in itemsL:
            Id = itemN.attrib["id"]
            print(f"{mtype} {Id}")
            count = itemN.xpath("count(//m:moduleItem)", namespaces=NSMAP)
            # print (f"SYD: {count} inside replace; should be 1")
            yield onItem(itemN=itemN, user=self.user)

    def runPlugin(self, *, plugin: Any, limit: int = -1) -> None:
        """
        runs the plugin which may change the db.
        Prints the number of changes that have been (act mode) or would have 
        been made (not act mode).

        EXPECTS
        * plugin: a plugin
        * limit (optional): defaults to -1 for no limit
        """
        Input = plugin.Input()
        limit = int(limit)
        count = int(0)
        for key in Input:
            print(f"INPUT {key}")
            query = plugin.search(Id=Input[key])
            query.validate(mode="search")
            # should validate the query inside replacer? Probably yes
            self.search(query=query, Id=Input[key])
            xpath = plugin.loop()
            moduleType = xpath.split("'")[1]  # not particularly generic
            # print (f"T{moduleType}")
            onItem = plugin.onItem()
            for payload in self.loop(xpath=xpath, onItem=onItem, mtype=moduleType):
                # print (f"XML {payload['xml']}") -> use file debug.xml instead
                # it's possible that payload is empty, but it has to exist
                if payload is not None:
                    if "xml" in payload:
                        m = Module(xml=payload["xml"])
                        m.validate()
                        count += 1
                        if self.act is True:
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
                                    referenceId=payload[
                                        "refId"
                                    ],  # do we need to pass refId or not?
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

    def search(self, *, query: Search, Id: int) -> None:
        """
        Performs a search, writes results to disk (for debugging and as cache) 
        and saves result in self.ET
        """
        out_fn = f"temp{Id}.zml.xml"
        if self.lazy is True and Path(out_fn).exists():
            print(f"Loading response for temp file {out_fn}")
            self.ET = Module(file=out_fn).toET()
        else:
            query.validate(mode="search")
            r = self.sar.search(query=query)  
            print(f" writing response to temp file: {out_fn}")
            r.toFile(path=out_fn)  
            self.ET = r.toET()

"""
    For a given search query, return the results. If the number of results 
    exceeds the chunkSize, return multiple chunks. For now, we only allow very
    limited set of search queries based on a single id (group, exhibit, 
    location, approvalGrp).

    USAGE
    from Mp.Api.Chunky import Chunky
    for chunk in getByType(ID=ID, Type="group"): 
        do_something_with (chunk) # chunk is ET

    for chunk in search(query=query, offset=0):
        do_something_with (chunk) # chunk is ET

    THE PROBLEM 
    * A search returns more items (=results) than I can digest, i.e over 1 GB,
      i typically cant process xml files anymore.

    THE SOLUTION
    * to split up the response in chunks (aka blocks or pages) and to deal with
      them individually
    * in good old MPX tradition, we want independent chunks, i.e. the objects
      should be accompanied not by random Person and Multimedia records, but
      exactly by those that are referenced in the object records. So related
      items are those referenced from the object item. However, if the person 
      or multimedia items reference other persons and multimedia, we don't 
      include them, i.e. we're including only immediate relatives, no distant
      cousins.
    
    TOWARDS AN ALGORITHM
    A "deterministic" solution would first (1) query how many results there are
    and then (2) do further queries for every chunk until done. It turns out 
    that a deterministic algorithm would be very easy, b/c RIA reports the 
    total hits in the totalSize attribute.
    
    Example: 100 results, but chunk size is 10, so we make 10 chunks
    (in production we expect that chunk size should be between 1000 or 3000, in 
    development we're using a much smaller number to reduce the wait)
    
    What about an "undeterministic" solution, e.g. a solution where we don't 
    know the total number of results until we have gotten all results?

    Let's look for the simplest solution: A block is the last block if the 
    number of results is smaller than chunkSize (even if it is null).
    
    NOTES / QUESTIONS / DEFINITIONS
    * The chunky (=paginated) search is expected not to be faster than an 
      unchunked search since it will likely involve more http requests for the
      same thing.
    * We'll call the one-type response/document "a part" in contrast to 
      "chunk", which we'll reserve for multi-type documents.
    * We want a multi-type chunk, i.e. have objects, multimedia, and persons, 
      perhaps others in one chunk. 
    * I could hide which modules are included, or I can make it explicit. 
      Compromise would be a default value. On the other hand, this is not our 
      problem atm. Let's just bake Object, Multimedia and Person in and find 
      a proper solution later. In other words: We considered to provide another
      argument to specify the requested target modules, e.g.:
        mtype: List[str] = ['Object', 'Multimedia', 'Person']
      But we decided against it; this can be done later, if really of use.
    * This time I want to return document as etree, b/c in the long term I 
      expect that this solution will be faster than converting between etree 
      and string repeatedly.
    * Should we write chunks to disk? No
    * Let's experiment with type hints again; we're using Python 3.9 type hints
"""

from lxml import etree
from pathlib import Path
from typing import Any, Iterator, List, Union
from mpapi.search import Search
from mpapi.client import MpApi
from mpapi.helper import Helper
from mpapi.module import Module
from mpapi.sar import Sar

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

# types aliasses
ET = etree._Element
ETNone = Union[etree._Element, None]
since = Union[str, None]

# typed variables
baseURL: str
pw: str
user: str


class Chunky(Helper):
    def __init__(self, *, chunkSize: int, baseURL: str, pw: str, user: str) -> None:
        self.chunkSize = chunkSize
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)

    def getByType(
        self, *, ID, Type, since: since = None, offset: int = 0
    ) -> Iterator[Module]:
        """
        Get a pack based on approval [group], location, group or exhibit.
        Yields independent chunks.

        EXPECTS
        * ID:
        * Type: type of the ID (approval, location, group, exhibit) TODO
        * since: xs:DateTime (more or less)
        * offset: initial offset to ignore object hits

        RETURNS
        * iterator [chunk: Module]: an indepedent chunk with persons, 
          multimedia and objects
        """
        lastChunk: bool = False
        while not lastChunk:
            chunk = Module()  # make a new zml module document
            partET = self._getObjects(Type="group", ID=ID, offset=offset, since=since)
            chunk.add(doc=partET)

            # all related Multimedia and Persons items, no chunking
            for targetType in ["Multimedia", "Person"]:
                relatedET = self._relatedItems(
                    part=partET, target=targetType, since=since
                )
                if relatedET is not None:
                    chunk.add(doc=relatedET)

            offset = offset + self.chunkSize
            actualNo = chunk.actualSize(module="Object")
            # print(f"*** actual VS chunkSize: {actualNo} VS {self.chunkSize}")

            if actualNo < self.chunkSize:
                lastChunk = True
            yield chunk

    def search(self, query: Search, since: since = None, offset: int = 0):
        """
        We could attempt a general chunky search. Just hand over a search query
        (presumably one which finds object items). We split the results into
        chunks and add the related items to every chunk.

        TODO: test this
        """
        lastChunk: bool = False
        while not lastChunk:
            chunk = Module()  # make a new zml module document
            query.offset=offset # todo in search
            r = self.api.search(xml=query.toString())
            partET = etree.fromstring(r.content, ETparser)
            chunk.add(doc=partET)
            # all related Multimedia and Persons items, no chunking
            for targetType in ["Multimedia", "Person"]:
                relatedET = self._relatedItems(
                    part=partET, target=targetType, since=since
                )
                if relatedET is not None:
                    chunk.add(doc=relatedET)

            offset = offset + self.chunkSize
            actualNo = chunk.actualSize(module="Object")
            # print(f"*** actual VS chunkSize: {actualNo} VS {self.chunkSize}")

            if actualNo < self.chunkSize:
                lastChunk = True
            yield chunk

    #
    # private methods
    #

    def _getObjects(
        self, *, Type: str, ID: int, offset: int, since: since = None
    ) -> ET:
        """
        A part is the result from a single request, e.g. for one module type.
        EXPECTS
        * type: requested target module type
        * ID: of requested group
        * offset: offset for search query
        * since: dateTime string; TODO

        RETURNS
        * ET document

        NOTE
        * ATM this is a getByGroup query always, but a generic getPart query as
          the name of the method suggests.
        * Let's not return a Module object, b/c that simplifies the code
        """
        fields: dict = {  # TODO: untested
            "approval": "ObjPublicationGrp.TypeVoc",
            "group": "ObjObjectGroupsRef.__id",
            "loc": "ObjCurrentLocationVoc",
            "exhibit": "ObjRegistrarRef.RegExhibitionRef.__id",
        }

        s = Search(module="Object", limit=self.chunkSize, offset=offset)

        if since is not None:
            s.AND()

        s.addCriterion(
            field=fields[Type],
            operator="equalsField",
            value=str(ID),
        )

        if since is not None:
            s.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        # s.print()
        s.validate(mode="search")
        r = self.api.search(xml=s.toString())
        # print(f"status {r.status_code}")
        return etree.fromstring(r.content, ETparser)

    def _relatedItems(
        self, *, part: ET, target: str, since: since = None
    ) -> Union[ET, None]:
        """
        For a zml document, return all related items of the target type.

        EXPECTS
        * part as ET: input (object) data with references to related data
        * target:  target module type (either "Person" or "Multimedia")
        * since: TODO. Date to filter for updates

        RETURNS
        * etree document with related items of the target type
        """

        IDs: Any = part.xpath(
            f"//m:moduleReference[@targetModule = '{target}']/m:moduleReferenceItem/@moduleItemId",
            namespaces=NSMAP,
        )

        if len(IDs) == 0:
            # raise IndexError("No related IDs found!")?
            print(f"***No related {target} IDs found {IDs}")
            return None

        # use limit=0 for a deterministic search as RIA's response provides the
        # number of search results limit -1 not documented at
        # http://docs.zetcom.com/ws/ seems to return all results
        s = Search(module=target, limit=-1, offset=0)
        count = 1  # one-based out of tradition; counting unique IDs
        relIDs = set(IDs)  # IDs are not unique, but we want unique
        for ID in sorted(relIDs):
            # print(f"{target} {ID}")
            if count == 1 and len(relIDs) > 1:
                s.OR()
            s.addCriterion(
                operator="equalsField",
                field="__id",
                value=str(ID),
            )
            count += 1
            if since is not None:
                s.AND()
                s.addCriterion(
                    operator="greater",
                    field="__lastModified",
                    value=str(since),  # "2021-12-23T12:00:00.0"
                )
        s.toFile(path="debug.search.xml")
        # s.print()
        s.validate(mode="search")
        r = self.api.search(xml=s.toString())
        #DEBUG
        with open("DEBUGresponse.xml", "wb") as binary_file:
            # Write bytes to file
            binary_file.write(r.content)        
        return etree.fromstring(r.content, ETparser)
"""
    For a given search query, return the results. If the number of results 
    exceeds the chunkSize, return multiple chunks. For now, we only allow very
    limited set of search queries.

    Experimenting with a paginated search. Unfinished!

    The problem 
    * A search returns more items (=results) than I can digest

    The solution
    * to split up the response in chunks (aka blocks or pages) and to deal with
      them individually
    * in good old MPX tradition, we want independent chunks, i.e. the objects
      should be accompanied not by random Person and Multimedia records, but
      exactly by those that are referenced in the object records.
    
    TOWARDS AN ALGORITHM
    A "deterministic" solution would first (1) query how many results there are
    and then (2) do further queries for every chunk until done.
    
    Example: 100 results, but chunk size is 10, so we make 10 chunks
    (in production we expect that chunk size should be between 1000 or 3000, in 
    development we're using a much smaller number to reduce the wait)
    
    What about an "undeterministic" solution, e.g. a solution where we don't 
    know the total number of results until we have gotten all results?

    Let's look for the simplest solution: A block is the last block if the 
    number of results is smaller than chunkSize (even if it is null).
    
    Let's say there a 30 results and the chunkSize is 10. Then we get
    10 limit is 10; offset is 0 -> first chunk
    10 limit is 10; offset is 10 -> 2nd chunk
    10 limit is 10; offset is 20 -> 3rd chunk
    0 limit is 10; offset is 30; -> 4th chunk; 0 is smaller than chunkSize so 
    it's the last chunk

    NOTES / QUESTIONS / DEFINITIONS
    * The chunky (=paginated) search is expected not to be faster than an 
      unchunked search nice it will involve more http requests for the same
      thing.
    * Should we count chunks one-based?
    * We start with simple searches, but perhaps we generalize later, e.g. 
      requesting the objects from one group. More general would be a chunking
      mechanism for all searches.
    * We want a multi-type chunk, i.e. have objects, multimedia, and persons, 
      perhaps others in one chunk. I could hide that fact, or I can make it 
      explicit. Compromise would be a default value. On the others hand, this 
      is not our problem atm. Let's just bake Object, Multimedia and Person in
      and find a proper solution later. In other words: We considered to 
      provide another argument to specify the requested target modules, e.g.:
        mtype: List[str] = ['Object', 'Multimedia', 'Person']
      But we decided against it; this can be done later, if really of use.
    * This time I want to return document as etree, b/c in the long term I 
      expect that this solution will be faster than converting between etree 
      and xml string repeatedly.
    * Should we write chunks to disk? In Sar I left all disk operations to mink
      level. Should we still do that or should Chunky.py this time be able to 
      write to disk directly. Perhaps useful for testing. In general let's try
      stuff here differently from SAR.
    * Let's experiment with type hints again; we're using Python 3.9 type hints
    * We'll call the one-type response/document a part in contrast to chunk, 
      which we'll reserve for multi-type documents.

    INTERFACE PROPOSAL
    def byGroup (ID:int = ID) -> iterator[ET] # ID is groupID

    for chunk in byGroup (ID=ID): 
        do_something_with (chunk) # chunk is ET
  
"""

from lxml import etree  # type: ignore
from pathlib import Path
from typing import Iterator, NewType, Union
from MpApi.Search import Search
from MpApi.Client import MpApi
from MpApi.Module import Module
from MpApi.Sar import Sar
from MpApi.Helper import Helper

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

# types
since = Union[str, None]  # NewType ('since', Union[str, None]) gives mypy error
ET = etree._Element

# typed variables
baseURL: str
pw: str
user: str


class Chunky(Helper):
    def __init__(self, *, chunkSize: int, baseURL: str, pw: str, user: str) -> None:
        self.chunkSize = chunkSize
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        # self.baseURL = baseURL # dont need it yet
        # self.user = user # dont need it yet
        # self.sar = Sar(baseURL=baseURL, user=user, pw=pw)

    def getByType(self, *, ID, Type, since: since = None) -> Iterator[Module]:
        """
        Get a pack based on approval [group], location, group or exhibit.
        Yields independent chunks.

        EXPECTS
        * ID:
        * Type: type of the ID (approval, location, group, exhibit) TODO
        * since: TODO

        RETURNS
        *
        """

        lastChunk: bool = False
        offset: int = 0

        while not lastChunk:
            chunk = Module()  # make a new zml module document
            print(f"Getting {self.chunkSize} objects")
            # let's deal with exotic multi-type later

            print(f"ID:{ID} offset:{offset} since:{since}")
            partET = self._getObjects(Type="group", ID=ID, offset=offset, since=since)

            # print(
            #    etree.tostring(partET, pretty_print=True, encoding="unicode")
            # )

            chunk.add(doc=partET)  # chunk.add empties out partET

            # print(
            #    etree.tostring(partET, pretty_print=True, encoding="unicode")
            # )

            # all related Multimedia and Persons items, no chunking
            relMul = self._relatedItems(part=partET, target="Multimedia", since=since)
            # print(f"***relMul: {relMul}")
            if relMul is not None:
                chunk.add(doc=relMul)

            relPer = self._relatedItems(part=partET, target="Person", since=since)
            # print(f"***relPer: {relPer}")
            if relPer is not None:
                chunk.add(doc=relPer)

            # TODO: is it possible that Persons and Multimedia reference other Persons and Multimedia?
            # then these might be missing so far -> Let's ponder that first

            offset = offset + self.chunkSize
            actualNo = chunk.actualSize(module="Object")  # of object moduleItems
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
        fields: dict = {  # TODO
            "approval": "wrong.__id",
            "group": "ObjObjectGroupsRef.__id",
            "loc": "loc",
            "exhibit": "exhibit",
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

        IDs = part.xpath(
            f"//m:moduleReference[@targetModule = '{target}']/m:moduleReferenceItem/@moduleItemId",
            namespaces=NSMAP,
        )

        if len(IDs) == 0:
            # raise IndexError("No related IDs found!")?
            print(f"***No related {target} IDs found {IDs}")
            return

        # use limit=0 for a deterministic search as response provides the
        # number of search results limit -1 not documented at
        # http://docs.zetcom.com/ws/ seems to return all results
        s = Search(module=target, limit=-1, offset=0)
        count = 1  # one-based out of tradition
        relIDs = set(IDs)  # IDs are not unique, but we want unique
        for ID in sorted(relIDs):
            # print(f"{target} {ID}")
            if count == 1 and len(IDs) > 1:
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
        s.print()
        s.validate(mode="search")
        r = self.api.search(xml=s.toString())
        # print (f"status {r.status_code}")
        # print (r.content)
        return etree.fromstring(r.content, ETparser)


if __name__ == "__main__":
    with open("credentials.py") as f:
        exec(f.read())

    c = Chunky(chunkSize=1, baseURL=baseURL, pw=pw)
    cnt = 1  # 1-based counter
    for chunk in c.byGroup(ID=162397):  # chunk is ET
        chunk.toFile(path=f"o{cnt}.xml")
        print(f"Working on chunk no {cnt}")
        cnt += 1

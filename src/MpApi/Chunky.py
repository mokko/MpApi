"""
    For a given search query, return the results. If the number of results exceeds
    the chunkSize, return multiple chunks.

    Experimenting with a paginated search. Unfinished!

    The problem: A search returns more items (=results) than I can digest

    The solution: to split up the response in chunks (aka blocks or pages)
    and to deal with them individually.
    
    A deterministic solution
    1. First query: how many results are there?
    2. Further queries for every chunk
    
    Example: 100 results, but chunk size is 10, so we make 10 chunks
    (in production we expect that chunk size should be between 1000 or 3000, in 
    development we're using a much smaller number to reduce the wait)
    
    What about an undeterministic solution, e.g. a solution where we don't know the total
    number of results until we have gotten all results?

    The chunky (=paginated) search is expected not to be faster than an unchunked search 
    nice it may involve more http requests for the same thing.

    Let's look for the simplest solution: A block is the last block if the number of results
    is smaller than chunkSize.
    Let's say there a 30 results and the chunkSize is 10. Then we get
    10 limit is 10; offset is 0 -> first chunk
    10 limit is 10; offset is 10 -> 2nd chunk
    10 limit is 10; offset is 20 -> 3rd chunk
    0 limit is 10; offset is 30; -> 4th chunk; 0 is smaller than chunkSize so it's the last chunk  

    Should we count chunks one-based?

    We start with simple searches, but perhaps we generalize later, e.g. requesting the objects 
    from one group. More general would be to have a chunking mechanism for all searches.

    INTERFACE
    def byGroup (ID:int = ID) -> ETdocument # ID is groupID
    # mtype: List[str] = ['Object', 'Multimedia', 'Person'] considered, but discarded
    
    for chunk in byGroup (ID=ID):
        do_something_with (chunk)

    The chunk is supposed to be multi-type, i.e. have objects, multimedia, and persons, perhaps 
    others. I could hide that fact, or I can make it explicit. Compromise would be a default 
    value. On the others hand, this is not our problem atm. Let's just bake Object, Multimedia 
    and Person in and find a proper solution later.

    So internally we have to do something like this:
    get moduleItems of type "Object" for a certain groupID for first chunk
    get corresponding Multimedia items
    get corresponding Person items
    join them all together
    yield them
    continue with the next chunk 
    until we encounter a chunk that has less items than chunkSize
        
    This time I want to return document as etree, because in the long term I expect I that
    this solution will be quicker than always converting between etree and xml string.
    
    Should we write chunks to disk? In Sar I left all disk operations to mink level. Should we
    still do that or should Chunky.py this time be able to write to disk directly. Perhaps useful
    for testing.
"""

from lxml import etree
from pathlib import Path
from typing import Iterator, Union
from MpApi.Search import Search
from MpApi.Client import MpApi
from MpApi.Module import Module
from MpApi.Sar import Sar

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

# TYPES
Since = Union[str, None]
ET = etree._Element

baseURL: str
pw: str
user: str


class Chunky:
    def __init__(
        self, *, chunkSize: int, baseURL: str, pw: str
    ):  # dont know how to write return value -> Chunky
        self.chunkSize = chunkSize
        # self.baseURL = baseURL
        # self.user = user
        self.appURL = baseURL + "/ria-ws/application"
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        # self.auth = HTTPBasicAuth(user, pw)

    def byGroup(
        self, *, ID, since: Since = None
    ):  # , since:Since = None -> Iterator[ET]

        print("enter byGroup")

        lastChunk: bool = False
        offset: int = 0

        while not lastChunk:
            chunk: Module = (
                Module()
            )  # make a new zml document; should this class be called differently?
            for mtype in [
                "Object",
                "Multimedia",
                "Person",
            ]:  # lets deal with multi-type later
                print(f"module: {mtype}")
                part = self._getPart(module=mtype, offset=offset, since=since)
                chunk.join(doc=part)  # part is a Module object

            offset = offset + self.chunkSize
            if chunk.totalSize(module="Object") <= self.chunkSize:
                print("seems to be last chunk; setting lastChunk to True")
                lastChunk = True
            print("getting to yield")
            yield chunk.toET()  # not sure why

    def _getPart(self, *, module: str, offset: int, since: Since) -> Module:
        """
        A part is the result from a single request, e.g. for one module type.

        ATM this is a getByGroup query always, but a generic getPart query as the
        name of the method suggests.

        Let's return a Module object, not xml, not ET. Seems to be the cleanest
        interface.

        """
        fields: dict = {
            "Multimedia": "MulObjectRef.ObjObjectGroupsRef.__id",
            "Object": "ObjObjectGroupsRef.__id",
            "Person": "PerObjectRef.ObjObjectGroupsRef.__id",
        }

        s = Search(module=module, limit=self.chunkSize, offset=offset)

        if since is not None:
            s.AND()
        s.addCriterion(
            field=fields[module],
            operator="equalsField",
            value=id,
        )
        if since is not None:
            s.addCriterion(
                operator="greater",
                field="__lastModified",
                value=since,  # "2021-12-23T12:00:00.0"
            )
        s.validate(mode="search")

        req = self.api.search(xml=s.toString())
        xml = req.content()  # or .text?
        # partET = etree.fromstring(bytes(xml, "UTF-8"))
        partM = Module(xml=req.content())
        return partM


"""
    ----
    old notes
    ----
    - expects a search request as xml string as well as the block size;
      in production block size should default to 3000 or so. For developing we use
      a lower number.

    - returns a dictionary that is structured as follows
        block = {
            blockNo: 1,  # number of this block (1-based)
            blockSize: 3000, # nominal block size
            last: False,  # not the last block
            offset: 0  # (1-based)
            response: requestObject # payload
            resultsRunning: 3000  # number of results returned so far in this
                                  # and prev. blocks
        }

    We're trying not to use a deterministic algorithm to save some time:
        first request with least amount of fields just to determine the number of results
        further requests for each block with appropriate offset and size values

    Can we dispose of the first request and make the second request the first?
    Yes perhaps but then we only know number of total results when request is done.
    So we would need different return dict structure.

    Sort of a definition:
    A block is the last if the number of returns in a given block is smaller than
    the blockSize (or if the query for the next block does not return any results.
    So we may cache one block and look at the next one before we return the first.

    Note to self:
    In order to save cpu time, we might change the interface of MpAPI and SAR and
    pass around xml as etree instead of as string.

    We need a method to see the itemSize of a response
    Search module should allow updating offset value?
"""

if __name__ == "__main__":
    with open("credentials.py") as f:
        exec(f.read())

    c = Chunky(chunkSize=10, baseURL=baseURL, pw=pw)
    for chunk in c.byGroup(ID=20222):
        print(chunk)

"""
For a given search query, return the results. If the number of results exceeds
the chunkSize, return multiple chunks. For now, we only allow very limited set
of search queries based on a single id (group, exhibit, location, approvalGrp).

A chunk consists of, say, 1000 objects and their corresponding multimedia and
persons items. However, if the person or multimedia items reference other
persons and multimedia, we don't include them, i.e. we're including only
immediate relatives, no distant cousins. To be excplicit, we call this a multi-
part response in contrast with a single-part chunk that only contains items of
type object.

USAGE
    from Mp.Api.Chunky import Chunky
    c = Chunky(chunkSize=1000, baseURL=baseURL, pw=pw, user=user)
    for chunkM in c.getByType(ID=ID, Type="group"):
        do_something_with (chunkM)

    for chunkM in c.search(query=query, offset=0):
        do_something_with (chunkM)


TOWARDS AN ALGORITHM
A "deterministic" solution would first (1) query how many results there are
and then (2) do further queries for every chunk until done. It turns out that
a deterministic algorithm would be very easy, b/c RIA reports the total hits
in the totalSize attribute.

What about an "undeterministic" solution, e.g. a solution where we don't
know the total number of results until we have gotten all results?

Let's look for the simplest solution: A chunk is the last chunk if the number
of results is smaller than chunkSize.

NOTES / QUESTIONS / DEFINITIONS
* The chunky (=paginated) search is expected not to be faster than an
  unchunked search since it will likely involve more http requests for the
  same thing.
* I could hide which modules are included, or I can make it explicit.
  Compromise would be a default value. On the other hand, this is not our
  problem atm. Let's just bake Object, Multimedia and Person in and find
  a proper solution later. In other words: We considered to provide another
  argument to specify the requested target modules, e.g.:
    mtype: List[str] = ['Object', 'Multimedia', 'Person']
  But we decided against it; this can be done later, if really of use.
* Should we write chunks to disk? No. That's not chunky's job. Should be
  done by mink etc.
"""

from lxml import etree
from mpapi.client import MpApi
from mpapi.helper import Helper
from mpapi.module import Module
from mpapi.sar import Sar
from mpapi.search import Search
from typing import Any, Iterator

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

# types aliasses
ET = etree._Element
ETNone = etree._Element | None
since = str | None

# typed variables
baseURL: str
pw: str
user: str

allowed_types = ["approval", "exhibit", "group", "loc", "query"]


class Chunky(Helper):
    def __init__(self, *, chunkSize: int, baseURL: str, pw: str, user: str) -> None:
        self.chunkSize = chunkSize
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)

    def getByType(
        self,
        *,
        ID,
        Type,
        target="Object",
        since: since = None,
        offset: int = 0,
        onlyPublished: bool = False,
    ) -> Iterator[Module]:
        """
        Get a pack based on approval [group], loc[ation], group, exhibit or query.
        Yields independent chunks.

        EXPECTS
        * ID:
        * Type: type of the chunk and the ID (approval, exhibit, group, loc,
          query)
        * since: xs:DateTime (more or less)
        * offset: initial offset to ignore object hits
        * target: result module type (only used with query)

        RETURNS
        * iterator [chunk: Module]: an indepedent chunk with persons,
          multimedia and objects

        Note / New
        * no more attachments
        * Type here is ambiguous, sometimes it corresponds to modType (e.g. object); in
          other cases it doesn't reflect the modType of the returned results (e.g. query
          can return objects or persons.
        * Curently, we only allow saved queries that request Objects
        """
        if Type not in allowed_types:
            raise SyntaxError(f"Error: Chunk type not recognized: {Type}")

        lastChunk: bool = False
        while not lastChunk:
            chunkData = Module()  # new zml Module object
            if Type == "query":
                m = self._savedQuery(Type=target, ID=ID, offset=offset)
            else:
                m = self._getObjects(Type=Type, ID=ID, offset=offset, since=since)
            chunkData += m
            # only look for related data if there is something in current chunk
            if m:
                # all related Multimedia and Persons items, no chunking
                for targetType in ["Multimedia", "Person"]:
                    relatedM = self._relatedItems(
                        part=m.toET(),
                        target=targetType,
                        since=since,
                        onlyPublished=onlyPublished,
                    )
                    if relatedM:
                        chunkData += relatedM

            offset += self.chunkSize  # wrong for last chunk
            if chunkData.actualSize(module="Object") < self.chunkSize:
                lastChunk = True
            yield chunkData

    def search(
        self, query: Search, since: since = None, offset: int = 0
    ) -> Iterator[Module]:
        """
        We could attempt a general chunky search. Just hand over a search query
        (presumably one which finds object items). We split the results into
        chunks and add the related items to every chunk.

        TODO: test this
        """
        lastChunk: bool = False
        while not lastChunk:
            chunkData = Module()  # make a new zml module document
            query.offset(value=offset)  # todo in search
            m = self.api.search2(query=query)
            chunkData += m
            # all related Multimedia and Persons items, no chunking
            for targetType in ["Multimedia", "Person"]:
                relatedM = self._relatedItems(
                    part=partET, target=targetType, since=since
                )
                if relatedM:
                    chunkData += relatedM

            offset = offset + self.chunkSize
            # print(f"*** actual VS chunkSize: {actualNo} VS {self.chunkSize}")

            if chunkData.actualSize(module="Object") < self.chunkSize:
                lastChunk = True
            yield chunkData

    #
    # private methods
    #

    def _getObjects(
        self, *, Type: str, ID: int, offset: int, since: since = None
    ) -> Module:
        """
        A part is the result from a single request, e.g. for one module type.
        EXPECTS
        * Type: requested target module type
        * ID: of requested group
        * offset: offset for search query
        * since: dateTime string; TODO

        RETURNS
        * was: ET document, now Module

        NOTE
        * ATM this is a getByGroup query always, but a generic getPart query as
          the name of the method suggests.
        """
        fields: dict = {  # TODO: untested
            "approval": "ObjPublicationGrp.TypeVoc",
            "exhibit": "ObjRegistrarRef.RegExhibitionRef.__id",
            "group": "ObjObjectGroupsRef.__id",
            "loc": "ObjCurrentLocationVoc",
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
        # print(s.toString())
        s.validate(mode="search")
        return self.api.search2(query=s)

    def _relatedItems(
        self, *, part: ET, target: str, since: since = None, onlyPublished: bool = False
    ) -> Module:
        """
        For a zml document, return all related items of the target type.

        EXPECTS
        * part as ET: input (object) data with references to related data
        * target:  target module type (either "Person" or "Multimedia")
        * since: TODO. Date to filter for updates

        NEW
        * returns Module, not ET | None
        * avoid optional (mixed) return value
        """

        IDs: Any = part.xpath(
            f"//m:moduleReference[@targetModule = '{target}']/m:moduleReferenceItem/@moduleItemId",
            namespaces=NSMAP,
        )

        if len(IDs) == 0:
            print(f"***WARN: No related {target} IDs found!")  # this is not an ERROR
            return Module()

        # use limit=0 for a deterministic search as RIA's response provides the
        # number of search results limit -1 not documented at
        # http://docs.zetcom.com/ws/ seems to return all results
        s = Search(module=target, limit=-1, offset=0)
        relIDs = set(IDs)  # IDs are not necessarily unique, but we want unique
        count = 1  # one-based out of tradition; counting unique IDs
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
        if onlyPublished and target == "Multimedia":
            # UNTESTED!!!
            s.NOT()
            for each in [".mp3", ".pdf", ".wav", "mp4"]:
                s.addCriterion(
                    operator="endsWithTerm",
                    field="MulOriginalFileTxt",
                    value=each,
                )

        s.toFile(path="debug.search.xml")
        # s.print()
        s.validate(mode="search")
        return self.api.search2(query=s)

    def _savedQuery(self, *, Type: str = "Object", ID: int, offset: int = 0) -> Module:
        """
        returns the result of a saved query (limited to chunkSize)

        Is this correct? `Yes, we're calling this from getByType with various offsets.
        Each call returns the object part of the a chunk.
        """
        ET = self.api.runSavedQuery2(
            Type=Type, ID=ID, offset=offset, limit=self.chunkSize
        )
        return Module(tree=ET)

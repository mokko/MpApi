"""
    Experimenting with a paginated search. Unfinished!

    For a given search query, return the results. If the number of results exceeds
    the block (page) size, return the results in multiple blocks (chunks, pages).

    The paginated or block search is expected to be considerably slower than a
    normal search nice it necessessarily involves more http requests.

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
    the blockSize or if the query for the next block does not return any results.
    So we may cache one block and look at the next one before we return the first.

    Note to self:
    In order to save cpu time, we might change the interface of MpAPI and SAR and
    pass around xml as etree instead of as string.

    We need a method to see the itemSize of a response
    Search module should allow updating offset value?
"""

class ChunkySearch
    def searchBlocks(self, *, xml, size=30): pass

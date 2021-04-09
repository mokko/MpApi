"""
sar stands search and response. It's a higher level interface on top of MpApi that bundles 
multiple requests together, typically searches and responses. 

I introduce it mainly to clean up the code of the Mink class, so that Mink has to deal less 
with xml and Sar.py can be tested easier. Conversely, that means that mink parses DSL config 
file, writes files, reports to log and user. 

Typically returns a requests reponse r which contains xml in r.text or binary in
r.content. Do expose etree stuff to user at all?

A set is an xml containing a set of items.

xml stands for string-like binary representation.

USAGE:
    sr = Sar(baseURL=baseURL, user=user, pw=pw)

    #get something  from single ids
    r = sr.getItem(module="Objekt", id="1234")    # returns single item for any module
    r = sr.getObjectsSet(type="group", id="1234") # just Objekte, returns a set
    r = sr.getMediaSet(type="exhibit", id="1234") # just Multimedia, returns a set

    #find out about the last search
    s = sr.search                                 # returns the last search request as xml, if any

    #do something with sets
    for content in attachmentsIter(set=xml):
        # do something with content 
    
    #Helpers                   # quite different sort of stuff, could go to soemewhere else?
    joinZml(globber, out_fn)   # writes result to file
    xml = clean (xml)          # clean up xml so it validates and contains less sensitive info
"""

class Sar:
    def __init__(self): pass
    def getItem(self, *, module, id): pass
    def getMediaSet(self, *, id, type):
        """ 
        Get multimedia items for exhibits or groups; returns a requests object with xml 
        a document containing a set of item.
        """

    def getObjectsSet(self, *, id, type):
        """ Get object items for exhibits or groups"""

    def attachmentsIter(self, *, ): pass
    
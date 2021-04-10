"""
Sar stands "search and response". It's a higher level interface on top of MpApi that 
bundles multiple requests together, typically searches and responses. 

I introduce it mainly to clean up the code of the Mink class, so that Mink has to deal less 
with xml and Sar.py can be tested easier. (Conversely, that means that mink parses DSL config 
file, writes files, reports to log and user. 

Sar typically returns a requests reponse (r) which contains xml in r.text or binary in
r.content. 

Do we expose etree stuff to the user at all? 

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

    sr.search 

    #do something with sets
    for content in attachmentsIter(set=xml):
        # do something with content 
    
    
    #Helpers                   # quite different sort of stuff, could go to soemewhere else?
    joinZml(globber, out_fn)   # writes result to file
    xml = cleanZml (xml)       # clean up xml so it validates and contains less sensitive info

Sar : higher level operations with xml
MpApi : basic API operations 
Search | Module : make XML


"""
from Search import Search

class Sar:
    def __init__(self, *, baseURL=baseURL, user=user, pw=pw): 
        self.search = None # attrib for search requests
        self.api(baseURL=baseURL, user=user, pw=pw)
        
    def getItem(self, *, module, id): 
        """
        Get a single item of any module by id. Returns a request object.
        Doesn't set self.search.
        """
        r = self.api.getItem(module="Multimedia", id=id)
        return r

    def getMediaSet(self, *, id, type):
        """ 
        Get a set multimedia items for exhibits or groups; returns a requests object with a xml 
        document containing a set of item.
        """
        s = Search(module="Multimedia")
        if type == "exhibitId":
            s.addCriterion(
                    operator="equalsField",
                    field="Multimedia.MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
                    value=id)
        elif type == "groupId":
            s.addCriterion(
                operator="equalsField", 
                field="Multimedia.MulObjectRef.ObjObjectGroupsRef.__id", 
                value=id)
        else:
            raise ValueError("Unknown argument!")
        
        r = self.api.search(module="Multimedia", xml=s.toString())
        return r
        
    def getObjectsSet(self, *, id, type):
        """ Get object items for exhibits or groups"""

        s = Search(module="Object")
        if type == "exhibitId":
            s.addCriterion(
                operator="equalsField",
                field="ObjRegistrarRef.RegExhibitionRef.__id",
                value=id
            )
        elif type == "groupId":
            s.addCriterion(
                operator="equalsField", field="ObjObjectGroupsRef.__id", value=id
            )
        else:
            raise ValueError("Unknown argument!")
        s.validate(mode="search")
        self.search = s.toString()
        
    def attachmentsIter(self, *, ): pass
    
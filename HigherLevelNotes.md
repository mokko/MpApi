I want all records from objects in a group or exhibit.

My first attempt was something like this:

    s = Search(module="ObjectGroup")
    s.addCriterion(operator="equalsField", field="__id", value="29825")
    s.validate()
    s.toFile(path="../data/search.xml")
    r = api.search(module="ObjectGroup", et=s.et)
    api.toFile(response=r, path="../data/objectGroup.xml")
    ogr = ObjectGroup(xml=bytes(r.text, "utf8"))
    for each in ogr.items():
        print(each)
        obj = api.getItem(module="Object", ID=each[0])
        api.toFile(response=obj, path=f"../data/obj{each[0]}.xml")

So I search for a group, extract all items from the group and get those objects individually.
That process works, but is very slow. Also note the transparence issue. It's good to 
document the process, so I save the initial search and response as well as the records. 
Additionally, it could write a log file with the http responses.

So now I want to query the objects that are members of a group. Ideally, I would get the search 
the full objects as search results.

So how would the search look like. Let's search for the objects in exhibition 20222. 
It has 173 items. Object.ObjRegistrarRef.RegExhibitionRef.__id

---
* To create new records (items), I need to be able to make objects in xml from scratch.
* I need a test suite otherwise stuff will break hard.

* For me python is fine, but if others want to use it, I need a gui. 
* The thing could run locally, so no need for a server. 
* The thing could be used with local user rights.

* How to upload and download 
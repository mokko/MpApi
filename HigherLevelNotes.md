I want all records from objects in a group or exhibit.

My first attempt was something like this:

    s = Search(module="ObjectGroup")
    s.addCriterion(operator="equalsField", field="__id", value="29825")
    s.validate()
    s.write(path="../data/search.xml")
    r = api.search(module="ObjectGroup", et=s.et)
    api.write(response=r, path="../data/objectGroup.xml")
    ogr = ObjectGroup(xml=bytes(r.text, "utf8"))
    for each in ogr.items():
        print(each)
        obj = api.getItem(module="Object", ID=each[0])
        api.write(response=obj, path=f"../data/obj{each[0]}.xml")

So I search for a group, extract all items from the group and get those objects individually.
That process works, but is very slow. Also note the transparence issue. It's good to 
document the process, so I save the initial search and response as well as the records. 
Additionally, it could write a log file with the http responses.

So now I want to query the objects that are members of a group. Ideally, I would get the search 
the full objects as search results.

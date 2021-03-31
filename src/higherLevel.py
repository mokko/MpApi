from pathlib import Path
from Search import Search
from MpApi import MpApi
from Module import Module

with open("credentials.py") as f:
    exec(f.read())

class HigherLevel:

    def __init__(self): 
        print(f"{baseURL}:{user}:{pw}")
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        
    def newRecord(self):
        print ("*CHANGE RECORD")
        m = Module(name="Object")
        mi = m.moduleItem()
        m.dataField(parent=mi, name="ObjTechnicalTermClb", value="Zupftrommel")
        #m.dataField(parent=rgi, name="InventarNrSTxt", value="I C 7723")
        m.print()
        m.validate()

        r = self.api.newModuleItem(module="Object", xml=m.toString())
        print (r)

    def exhibitObjects (self):

        #mkdir project dir    
        project=Path("../sdata/exhibitObjects")
        if not project.exists():
            mkdir (project)
                
        #prepare search request
        s = Search(module="Object")
        s.addCriterion(operator="equalsField", field="ObjRegistrarRef.RegExhibitionRef.__id", value="20222")
        s.print()
        s.validate()
        s.toFile(path=project.joinpath("search.xml"))
    
        #request and response
        r = self.api.search(module="Object", et=s.et)
        self.api.toFile(response=r, path=project.joinpath("response.xml"))

    def objectsViaGroup (self):

        #mkdir project dir    
        project = Path("../sdata/objectsViaGroup")

        #prepare search request
        s = Search(module="ObjectGroup")
        s.addCriterion(operator="equalsField", field="__id", value="29825")
        s.validate()
        s.toFile(path=project.joinpath("search.xml"))
   
        #request and response
        r = api.search(module="ObjectGroup", et=s.et)
        api.toFile(response=r, path="../data/objectGroup.xml")
        ogr = ObjectGroup(xml=bytes(r.text, "utf8"))
        for each in ogr.items():
            print(each)
            obj = api.getItem(module="Object", ID=each[0])
            self.api.toFile(response=obj, path= project.joinpath(f"obj{each[0]}.xml"))

if __name__ == "__main__":
    hl = HigherLevel()
    hl.newRecord()
    #hl.exhibitObjects()
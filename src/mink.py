"""
mink.py: Commandline frontend for MpApi.py

CLI USAGE
    cd projectData
    mink.py -j job 

DIR STRUCTURE    
projectData
    credentials.py
    HFObjekte/20210401/
        report.log
        response.xml
        response-join.xml
        search.xml
        ...
    jobs.dsl

CLASS USAGE
    m = Mink(conf="jobs.dsl", "job="tjob")

# mink domain-specific language (DSL)
HFObjekte:                  # makes dirs "HFobjekte/20210401" (with current date) 
                            # relative to pwd, 
    getObjects:
        exhibitId: 20222    # search0.xml, response0.xml
        groupID: 12345      # search1.xml, response1.xml
    #join (implicit)        # response-join.xml, if more than onr getObject
    clean                   # response-clean.xml
    validate                # log and print results: report.log
    digitalAssets
"""
import datetime
import logging
from Module import Module
from MpApi import MpApi
from pathlib import Path
from Search import Search
from lxml import etree # necessary?

with open("credentials.py") as f:
    exec(f.read())

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module"
    }


class Mink:
    def __init__(self, *, conf, job):
        self.job = job
        job_DF = None # definition in conf file
        mlc = False   # multiline command; not used, to clarify intent
        cmd = []
        args = []

        #pretty ugly dsl parser...
        with open(conf, mode="r") as file:
            c = 0  # line counter
            error = 0
            for line in file:
                c += 1
                uncomment = line.split("#", 1)[0].strip()
                if not uncomment:
                    continue
                line = line.expandtabs(4)
                indent_lvl = int((len(line) - len(line.lstrip())+4)/4)
                parts = uncomment.split()
                if indent_lvl == 1: #job label
                    if not parts[0].endswith(":"):
                        raise TypeError ("Job label has to end with colon") 
                    job_DF = parts[0][:-1]
                    if job_DF == job:
                        right_job = True
                        self._mkdirs()
                        self._init_log()
                        self._info(f"Project dir: {self.project_dir}")

                    else:
                        right_job = False
                    continue
                elif indent_lvl == 2: 
                    if parts[0].endswith(":"):
                        mlc = True
                        cmd = parts[0][:-1]
                        continue
                    else:
                        mlc = False
                        cmd = parts[0]
                        if len(parts)>1:
                            args = parts[1:]
                        else:
                            args = []
                    if right_job is True:
                        #print(f"**{cmd} {args}")
                        getattr(self,cmd)(args)
                elif indent_lvl == 3:
                    args = parts 
                    if right_job is True:
                        #print (f"**{cmd} {args}")
                        getattr(self,cmd)(args)

    def getObjects(self, args):
        """
        Use existing files as cache; i.e. only make new equests, if files don't exist yet.
        
        That means you needto manually delete files like search.xml and response.xml in
        your project dir if you want to do a new request.
        
        Speed is really bad. I wonder if Zetcom server supports compression.
        """
       
        #making search request
        id = args[1]
        out = args[2] #something unique
        self._info(f"GetObjects: {args[0]} {id} {out}")
        search_fn = self.project_dir.joinpath("search"+out+".xml")
        if search_fn.exists():
            self._info(f" Loading existing SEARCH request ({search_fn})")
            s = Search(fromFile=search_fn)
        else:
            s = Search(module="Object")
            if args[0] == "exhibitId":
                s.addCriterion(operator="equalsField", 
                    field="ObjRegistrarRef.RegExhibitionRef.__id", value=id)
            elif args[0] == "groupId":
                s.addCriterion(operator="equalsField", 
                    field="ObjObjectGroupsRef.__id", value=id)
            else:
                raise ValueError("Unknown argument!")
            s.validate(mode="search")
            self._info(" Search validates")
            s.toFile(path=search_fn) #overwrites old files
            self._info(f" Search request saved to {search_fn}")
        
        request_fn = self.project_dir.joinpath("response"+out+".xml")
        if request_fn.exists():
            self._info(f" Loading existing REQUEST file ({request_fn})")
        else:
            self._info(" About to execute new search request")
            api = MpApi(baseURL=baseURL, user=user, pw=pw)
            r = api.search(module="Object", xml=s.toString())
            self._info(f" Status: {r.status_code}")

            #lxml's pretty printer
            tree = etree.fromstring(bytes(r.text, "utf8"), ETparser)
            etree.indent(tree)
            root = etree.ElementTree(tree)
            root.write(str(request_fn), pretty_print=True) #only works on tree, not Element? 
            self._info(f" New response written to {request_fn}")

    def clean(self, out_path):
        print (f"clean {out_path}")
    
    def digitalAssets(self, out_path):
        print (f"da {out_path}")

    def join(self, out_path):
        """
        Join reponse*.xml and write it to out_path.

        For now, we assume that the module/@name is the same. 
        """
        out_fn = self.project_dir.joinpath(out_path[0])
        if out_fn.exists():
            self._info(f"join exists already, no overwrite {out_fn}")
        else:
            self._info(f"join file doesn't exist yet, making new one {out_fn}")
            
            first=None
            for each in self.project_dir.glob('response*.xml'):
                print (each)
                if first is None:
                    first = etree.parse (str(each), ETparser)
                    type = "Object" # cheating
                else:
                    responseTree = etree.parse (str(each), ETparser)
                    newItems = responseTree.xpath(
                        f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem", 
                        namespaces=NSMAP
                    )
                    if len(newItems)>0:
                        lastItem = first.xpath(
                            f"/m:application/m:modules/m:module[@name = '{type}']", 
                            namespaces=NSMAP
                            )[-1]
                        print(f":::{len(newItems)}")
                        for eachN in newItems:
                            lastItem.append(eachN)
                        items = first.xpath(
                            f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem", 
                            namespaces=NSMAP
                        )
                        print(f"****{len(items)}")
                        first.write(str(out_fn), pretty_print=True) 


    def validate(self, out_path):
        print (f"val {out_path}")

    #
    # PRIVATE HELPERS
    #

    def _info(self, msg):
        logging.info (msg)
        print(msg)

    def _init_log(self):
        log_fn = Path(self.project_dir).joinpath("report.log")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="w", # not append, start new file every time
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )

    def _mkdirs(self):
        date = datetime.datetime.today().strftime ('%Y%m%d')
        dir = Path(self.job).joinpath(date)
        if not Path.is_dir(dir):
            Path.mkdir (dir, parents=True)
        self.project_dir = dir

        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()

    m = Mink(job=args.job, conf=args.conf)
"""
mink.py: Commandline frontend for MpApi.py

CLI USAGE
    cd projectData
    mink.py -j job 

CONFIGURATION
    credentials.py   # put it out of harm's way 
    jobs.dsl         # defines/describes multiple jobs; expected in project dir 

DIR STRUCTURE    
    projectData              # <-- use it as working directory (pwd)
        ajob/20210401        # <-- project dir
            report.log
            response.xml
            response-join.xml
            search.xml
            ...
        credentials.py       # use protection (e.g. .gitignore)
        jobs.dsl             # expected in pwd

CLASS USAGE
    m = Mink(conf="jobs.dsl", "job="ajob") # parses jobs.dsl and runs commands listed there
    m.clean(args) # list with in and out file
    m.digitalAssets(args) # list with in file
    m.getObjects(args)
    ...

"""
import datetime
import logging
from Module import Module
from MpApi import MpApi
from pathlib import Path
import requests
from Search import Search
from lxml import etree  # necessary?

with open("credentials.py") as f:
    exec(f.read())

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Mink:
    def __init__(self, *, conf, job):
        self.job = job
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)

        job_DF = None   # definition in conf file
        mlc = False     # multiline command; not used, to clarify intent
        cmd = []
        args = []
        any_job = False
        # pretty ugly dsl parser...
        with open(conf, mode="r") as file:
            c = 0  # line counter
            error = 0
            for line in file:
                c += 1
                uncomment = line.split("#", 1)[0].strip()
                if not uncomment:
                    continue
                line = line.expandtabs(4)
                indent_lvl = int((len(line) - len(line.lstrip()) + 4) / 4)
                parts = uncomment.split()
                if indent_lvl == 1:  # job label
                    if not parts[0].endswith(":"):
                        raise TypeError("Job label has to end with colon")
                    job_DF = parts[0][:-1]
                    if job_DF == job:
                        right_job = True
                        any_job = True
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
                        if len(parts) > 1:
                            args = parts[1:]
                        else:
                            args = []
                    if right_job is True:
                        # print(f"**{cmd} {args}")
                        getattr(self, cmd)(args)
                elif indent_lvl == 3:
                    args = parts
                    if right_job is True:
                        # print (f"**{cmd} {args}")
                        getattr(self, cmd)(args)
                
        if any_job is False:
            print(f"WARNING: User-supplied job didn't match any job in the job definition file!")

    def clean(self, args):
        """
        Strip certain elements out of response.xml so that it validates and is easier to
        read.
        Eliminates virtual fields, @uuid, Werte & Versicherungen. Used to eliminates
        also system fields, but still need those.
        """
        in_fn = self.project_dir.joinpath(args[0])
        out_fn = self.project_dir.joinpath(args[1])
        print (f"Clean in:{in_fn} out:{out_fn}")
        if out_fn.exists():
            self._info(" clean file exists already, no overwrite")
        else:
            self._info(f" making new clean file")
            
            m = Module(file=in_fn)
            for mi in m.iter(): 
                m.attribute(parent=mi, name="uuid", action="remove")
                m._rmUuidsInReferenceItems(parent=mi)
                m._dropRG(parent=mi, name="ObjValuationGrp")
                #m._dropFields(
                #    parent=mi, type="virtualField"
                #)  # if no parent, assume self.etree
            m.validate()
            self._info(" clean document validates")
            m.toFile(path=out_fn)
            self._info(f" clean document written ({out_fn})")

    def join(self, args):
        """
        Join multiple documents and write them to new file. Expects globbing 
        expression at args[0] and a filename at args[1] for the output.
        Output will be added to project directory path, so don't supply full
        file path. 

        Should work with multiple random item types now.
        
        Doesn't overwrite existing files as usual, so delete manually as usual.
        Normal log policy. No explicit return value.
        """
        known_types = set()
        glob_expr = args[0]
        out_fn = self.project_dir.joinpath(args[1])
        self._info(f"JOIN {glob_expr} {out_fn}")
        if out_fn.exists():
            self._info(f" join file exists already, no overwrite: {out_fn}")
        else:
            self._info(f" join file doesn't exist yet, making new one {out_fn}")
            firstET = None
            for eachFile in sorted(self.project_dir.glob(glob_expr)):
                self._info(f" joining {eachFile}")
                eachET = self.etreeFromFile(path=eachFile)
                moduleL = eachET.xpath(
                    f"/m:application/m:modules/m:module",
                    namespaces=NSMAP,
                )
                for moduleN in moduleL:
                    moduleA = moduleN.attrib
                    known_types.add(moduleA['name'])
                if firstET is None:
                    firstET = eachET
                else: 
                    for type in known_types:
                        newItemsL = eachET.xpath(
                            f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem",
                            namespaces=NSMAP,
                        )
                        if len(newItemsL) > 0: #only append if there is something to append
                            #print(f"type: {type}")
                            try:
                                lastModuleN = firstET.xpath(
                                    f"/m:application/m:modules/m:module[@name = '{type}']",
                                    namespaces=NSMAP
                                )[-1]
                            except:
                                #make a node with the write type
                                modulesN = firstET.xpath(
                                    f"/m:application/m:modules",
                                    namespaces=NSMAP
                                )[-1]
                                lastModuleN = etree.SubElement(modulesN, "{http://www.zetcom.com/ria/ws/module}module", name=type)
                            #print(f"len:{len(lastModuleN)} {lastModuleN}")
                            for newItemN in newItemsL:
                                lastModuleN.append(newItemN)
            for type in known_types: #update totalSize for every type
                itemsL = firstET.xpath(
                    f"/m:application/m:modules/m:module[@name = '{type}']/m:moduleItem",
                    namespaces=NSMAP
                )
                moduleN = firstET.xpath(
                    f"/m:application/m:modules/m:module[@name = '{type}']",
                    namespaces=NSMAP
                )[0]
                attributes = moduleN.attrib
                attributes['totalSize'] = str(len(itemsL))
            #write once when you're done joining files
            self.etreeToFile(ET=firstET, path=out_fn)
            self._info(f"join file written ({out_fn})")

    def getItem(self, args):
        module = args[0]
        id = args[1]
        out_fn = self.project_dir.joinpath(args[2])
        if not out_fn.exists():
            self._info(f"GetItem module={module} id={id} out_fn={out_fn}")
            r = self.api.getItem(module="Multimedia", id=id)
            self.xmlToFile(xml=r.text, path=out_fn)

    def getMultimedia(self, in_fn):
        """
        Get multimedia metadata and files.

        Parse an input xml file for multimedia moduleReferences, get all multimedia
        items having attachments and save those to disk using mm{id}.xml filename. 
        
        Also save their attachments using {mmId}.{extension} filename.
        """

        print(f"GetMultimedia {in_fn[0]}")
        in_fn=self.project_dir.joinpath(in_fn[0])
        #Download all mmItems which have an attachment
        mmTree = etree.parse(str(in_fn), ETparser)
        #seems the thumbnail info cannot be trusted or is irrelevant
        #[m:dataField/@name = 'ThumbnailBoo' and m:dataField/m:value = 'true']
        mmL = mmTree.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/m:moduleReference[@name = 'ObjMultimediaRef']" +
            "/m:moduleReferenceItem", namespaces=NSMAP)
        for mm in mmL:
            #print(etree.tostring(mm, pretty_print=True, encoding="unicode"))
            a = mm.attrib
            mmId = a["moduleItemId"]
            mmpath = self.project_dir.joinpath(f"mm{mmId}.xml")
            if mmpath.exists():
                #self._info(f" mm data exists already, not getting it again ({path})")
                mmT = self.etreeFromFile(path=mmpath)
            else:
                self._info(f"requesting multimediaItem {mmId}")
                r = self.api.getItem(module="Multimedia", id=mmId)
                self._info(f"{r.status_code}, about to write to disk")
                mmT = self.xmlToEtree(xml=r.text)
                self.etreeToFile(ET=mmT, path=mmpath)
            
            itemsL = mmT.xpath("/m:application/m:modules/m:module[@name='Multimedia']/m:moduleItem"+
                "[@hasAttachments = 'true']", namespaces=NSMAP) 
            for itemN in itemsL:
                itemA = itemN.attrib
                mmId = itemA["id"]
                fn_old = itemN.xpath("m:dataField[@name = 'MulOriginalFileTxt']/m:value/text()", 
                    namespaces=NSMAP)[0] #assuming that there can be only one
                fn = mmId+Path(fn_old).suffix
                mmpath = self.pix_dir.joinpath(fn)
                #print(f"****{fn}")
                if not mmpath.exists():    
                    r = self.api.getAttachment(module="Multimedia", id=mmId)
                    #fn = Path(r.headers["Content-Disposition"].split("=")[1])
                    #path = self.pix_dir.joinpath(mmId+fn.suffix)
                    self._info(f"About to write attachment to disk ({fn})")
                    with open(mmpath, "wb") as f:
                        f.write(r.content) # memory?

            
    def getObjects(self, args):
        """
        Use existing files as cache; i.e. only make new equests, if files don't exist yet.

        That means you needto manually delete files like search.xml and response.xml in
        your project dir if you want to do a new request.

        Speed is really bad. I wonder if the Zetcom server supports compression.
        """

        # making search request
        id = args[1]
        out = args[2]  # something unique
        self._info(f"GetObjects: {args[0]} {id} {out}")
        search_fn = self.project_dir.joinpath(f"search-objects{out}.xml")
        if search_fn.exists():
            self._info(f" loading existing SEARCH request ({search_fn})")
            s = Search(fromFile=search_fn)
        else:
            s = Search(module="Object")
            if args[0] == "exhibitId":
                s.addCriterion(
                    operator="equalsField",
                    field="ObjRegistrarRef.RegExhibitionRef.__id",
                    value=id,
                )
            elif args[0] == "groupId":
                s.addCriterion(
                    operator="equalsField", field="ObjObjectGroupsRef.__id", value=id
                )
            else:
                raise ValueError("Unknown argument!")
            s.validate(mode="search")
            self._info(" search validates")
            s.toFile(path=search_fn)  # overwrites old files
            self._info(f" search request saved to {search_fn}")

        request_fn = self.project_dir.joinpath(f"objects{out}.xml")
        if request_fn.exists():
            self._info(f" loading existing REQUEST file ({request_fn})")
        else:
            self._info(" about to execute new search request")
            r = self.api.search(module="Object", xml=s.toString())
            self._info(f" Status: {r.status_code}")

            self.xmlToFile(xml=r.text, path=request_fn)
            self._info(f" New response written to {request_fn}")

    def validate(self, out_path):
        """not necessary at the moment; would probably use Module.py"""
        print(f"val {out_path}")

    #
    # PUBLIC AND PRIVATE HELPERS
    #

    def _info(self, msg):
        logging.info(msg)
        print(msg)

    def _init_log(self):
        log_fn = Path(self.project_dir).joinpath("report.log")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="w",  # not append, start new file every time
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )

    def _mkdirs(self):
        date = datetime.datetime.today().strftime("%Y%m%d")
        dir = Path(self.job).joinpath(date)
        if not Path.is_dir(dir):
            Path.mkdir(dir, parents=True)
        self.project_dir = dir
        self.pix_dir = dir.joinpath("..").joinpath("pix").resolve()
        if not self.pix_dir.exists():
            self._info(f"Making pix dir: {self.pix_dir}")
            Path.mkdir(self.pix_dir)

    def xmlToEtree(self, *, xml):
        tree = etree.fromstring(bytes(xml, "utf8"), ETparser)
        etree.indent(tree)
        return etree.ElementTree(tree)

    def xmlToFile(self, *, xml, path):
        """
        Pretty print and write to disk; expects xml.

        If you already have an etree, you could write to file in one
        line, not sure if we need a method for that.
        """
        tree = self.xmlToEtree (xml=xml)
        tree.write(str(path), pretty_print=True)  # only works on tree, not Element?

    def etreeFromFile(self, *, path):
        return etree.parse(str(path), ETparser)

    def etreeToFile (self, *, ET, path):
        ET.write(str(path), pretty_print=True)  # only works on tree, not Element?

    def etreePrint (self, *, ET):
        print(etree.tostring(ET, pretty_print=True))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()

    m = Mink(job=args.job, conf=args.conf)

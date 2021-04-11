# -*- coding: utf8
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
            variousFiles.xml
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
from Sar import Sar
from pathlib import Path
import requests
from Search import Search
from lxml import etree  # necessary?

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Mink:
    def __init__(self, *, conf, job, baseURL, user, pw):
        self.job = job
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)

        self.current_job = None  # definition in conf file
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
                    self.current_job = parts[0][:-1]
                    if self.current_job == job:
                        right_job = True
                        any_job = True
                        self._mkdirs()  # also sets project_dir etc.
                        self._init_log()
                        self.info(f"Project dir: {self.project_dir}")
                    else:
                        self.project_dir = Path(".")
                        right_job = False
                    continue
                elif indent_lvl == 2:
                    cmd = parts[0]
                    if len(parts) > 1:
                        args = parts[1:]
                    else:
                        args = []
                    if right_job is True:
                        # print(f"**{cmd} {args}")
                        getattr(self, cmd)(args)
                elif indent_lvl > 2:
                    print(f"indent lvl: {indent_lvl} {parts}")
                    raise TypeError("Too many indents in config file")

        if any_job is False:
            print(
                f"WARNING: User-supplied job didn't match any job from the definition file!"
            )

    def getItem(self, args):
        """
        Expects list of two arguments: module and id;
        returns response.text as xml.

        Makes a new response only if no cached requests already on disk.
        """
        module = args[0]
        id = args[1]
        out_fn = self.project_dir.joinpath(args[1] + ".xml")
        if not out_fn.exists():
            self.info(f"GetItem module={module} id={id} out_fn={out_fn}")
            r = self.sar.getItem(module=module, id=id)
            self.xmlToFile(xml=r.text, path=out_fn)
            return r.text
        else:
            print("File exists already; no overwrite")
            return str(self.xmlFromFile(path=out_fn))

    def getPackage(self, args):
        """
        Download object and related information (attachment, media, people).
        Expects a type (exhibit or group) and a corresponding id
        """
        print(f"getPackage {args}")

        type = args[0]
        id = args[1]
        label = args[2]
        sar = self.sar
        objX = None
        mmX = None
        pkX = None
        joinX = None
        # getting objects
        obj_fn = self.project_dir.joinpath(f"{label}-obj-{type}{id}.xml")
        if obj_fn.exists():
            self.info(f"Getting objects from file cache {obj_fn}")
            objX = self.xmlFromFile(path=obj_fn)
        else:
            self.info(f"Getting objects, saving to {obj_fn}")
            r = sar.getObjectSet(type=type, id=id)
            self.xmlToFile(xml=r.text, path=obj_fn)
            objX = r.text

        # getting media
        mm_fn = self.project_dir.joinpath(f"{label}-mm-{type}{id}.xml")
        if mm_fn.exists():
            self.info(f"Getting media from file cache {mm_fn}")
            mmX = self.xmlFromFile(path=mm_fn)
        else:
            self.info(f"Getting media, saving to {mm_fn}")
            r = sar.getMediaSet(type=type, id=id)
            self.xmlToFile(xml=r.text, path=mm_fn)
            mmX = r.text

        # saving attachments
        self.info(f"Getting attachments saving to {self.pix_dir}")
        self.sar.saveAttachments(xml=mmX, dir=self.pix_dir)
        # todo we probably want to delete those files that are no longer attached to media
        # just to do a better update

        # getting actors
        pk_fn = self.project_dir.joinpath(f"{label}-pk-{type}{id}.xml")
        if pk_fn.exists():
            self.info(f"Getting actors from file cache {pk_fn}")
            pkX = self.xmlFromFile(path=pk_fn)
        else:
            self.info(f"Getting actors, saving to {pk_fn}")
            r = sar.getActorSet(type=type, id=id)
            self.xmlToFile(xml=r.text, path=pk_fn)
            pkX = r.text

        # joining
        join_fn = self.project_dir.joinpath(f"{label}-join-{type}{id}.xml")
        if join_fn.exists():
            self.info(f"Getting join from file cache {join_fn}")
            joinX = self.xmlFromFile(path=join_fn)
        else:
            self.info(f"Joining objects, media and actors, saving to {join_fn}")
            joinX = sar.join(inL=[objX, mmX, pkX])
            self.xmlToFile(xml=joinX, path=join_fn)
        del objX, mmX, pkX  # saves some memory perhaps

        # cleaning
        clean_fn = self.project_dir.joinpath(f"{label}-clean-{type}{id}.xml")
        if clean_fn.exists():
            self.info(f"Getting clean from file cache {clean_fn}")
            cleanX = self.xmlFromFile(path=clean_fn)
        else:
            self.info(f"Cleaning join, saving to {clean_fn}")
            cleanX = sar.clean(inX=joinX)
            self.xmlToFile(xml=cleanX, path=clean_fn)
            self.info(" clean validates")
        # del joinX #at this point not necessary

    #
    # PRIVATE HELPERS
    #

    def info(self, msg):
        logging.info(msg)
        print(msg)

    def _init_log(self):
        log_fn = Path(self.project_dir).joinpath("report.log")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="a",  # append now since we're starting a new folder
            # every day now anyways.
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
            self.info("Making pix dir: {self.pix_dir}")
            Path.mkdir(self.pix_dir)

    def xmlFromFile(self, *, path):
        with open(path, "r", encoding="utf8") as f:
            xml = f.read()
        return xml

    def xmlToEtree(self, *, xml):
        tree = etree.fromstring(bytes(xml, "utf-8"), ETparser)
        # etree.indent(tree)
        return etree.ElementTree(tree)

    def xmlToFile(self, *, xml, path):
        """
        Write xml to disk; expects xml as string.
        """
        with open(path, "w", encoding="utf8") as f:
            f.write(xml)

        # tree = self.xmlToEtree (xml=xml)
        # tree.write(str(path), pretty_print=True)  # only works on tree, not Element?

    def etreeFromFile(self, *, path):
        return etree.parse(str(path), ETparser)

    def etreeToFile(self, *, ET, path):
        ET.write(
            str(path), pretty_print=True, encoding="UTF-8"
        )  # encoding is important!

    def etreePrint(self, *, ET):
        print(etree.tostring(ET, pretty_print=True))


if __name__ == "__main__":
    import argparse

    with open("../sdata/credentials.py") as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()

    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)

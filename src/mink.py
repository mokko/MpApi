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
from lxml import etree  # necessary?
import os
from pathlib import Path
import requests
import sys

# what the heck?
if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])
credentials = "credentials.py"  # expect credentials in pwd


from MpApi.Module import Module
from MpApi.Sar import Sar
from MpApi.Search import Search

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Mink:
    def __init__(self, *, conf, job, baseURL, user, pw):
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.conf = conf
        self._parse_conf(job=job)

    def _parse_conf(self, *, job):
        self.job = job
        self.current_job = None  # definition in conf file
        cmd = []
        args = []
        any_job = False
        # pretty ugly dsl parser...
        # todo: ignore empty line
        with open(self.conf, mode="r") as file:
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

    #
    # mink commands
    #

    def all(self, args):
        self._parse_conf(job=args[0])

    def clean(self, args):
        type = args[0]
        id = args[1]
        label = args[2]
        join_fn = self.parts_dir.joinpath(f"{label}-join-{type}{id}.xml")
        clean_fn = self.project_dir.joinpath(f"{label}-clean-{type}{id}.xml")
        if clean_fn.exists():
            print(f" clean from cache {clean_fn}")
            cleanX = self.xmlFromFile(path=clean_fn)
        else:
            self.info(f" cleaning join, saving to {clean_fn}")
            joinX = self.xmlFromFile(path=join_fn)
            cleanX = self.sar.clean(inX=joinX)
            self.xmlToFile(xml=cleanX, path=clean_fn)
            self.info(" clean validates")  # validation is part of clean
        return cleanX

    def definition(self, args):
        dfX = self.sar.definition()
        print("Writing to definition.xml")
        self.xmlToFile(xml=dfX, path="definition.xml")

    def getAttachments(self, args):
        print(f"***{args}")
        Type = args[0]
        Id = args[1]
        label = args[2]
        try:
            args[3]
        except:
            print(" not downloading attachments")
        else:  # executed if no exceptions were raised in the try block.
            att = str(args[3]).lower().strip()
            # print (f"GET HERE!{att}")
            if att == "attachments":
                # pretty dirty: assumes that getMedia has been done before
                mm_fn = self.parts_dir.joinpath(f"{label}-Multimedia-{Type}{Id}.xml")
                mmX = self.xmlFromFile(path=mm_fn)

                pix_dir = Path(
                    f"{self.pix_dir}_{label}"
                )  # this is a new dir, cannot be made earlier
                if not pix_dir.exists():
                    pix_dir.mkdir()
                print(f" checking attachments; saving to {pix_dir}")
                try:
                    expected = self.sar.saveAttachments(xml=mmX, adir=pix_dir)
                except Exception as e:
                    self.info("Error during saveAttachments")
                    raise e

                # do we want to delete those files that are no longer attached?
                for img in os.listdir(pix_dir):
                    img = Path(pix_dir).joinpath(img)  # need resolve here
                    if img not in expected:
                        print(f"image no longer attached, removing {img}")
                        os.remove(img)
        # currently we dont get attachments that have changed, but keep the same mulId,
        # that case should be rare

    def getExhibit(self, args):
        return self._getPart(
            id=args[1], label=args[2], module="Exhibition", type=args[0]
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
        if out_fn.exists():
            print(f" Item from cache {out_fn}")
            return str(self.xmlFromFile(path=out_fn))
        else:
            self.info(f"getItem module={module} id={id} out_fn={out_fn}")
            r = self.sar.getItem(module=module, id=id)
            self.xmlToFile(xml=r.text, path=out_fn)
            return r.text

    def getMedia(self, args):
        """
        get media records for exhibit or group, saving it to disk
        get attachments for that set of media records saving them to disk
        return media records as mmX
        """
        return self._getPart(
            id=args[1], label=args[2], module="Multimedia", type=args[0]
        )

    def getObjects(self, args):
        """
        expects [type, id] where type can any module (Object, Multimedia ...)
        """
        return self._getPart(id=args[1], label=args[2], module="Object", type=args[0])

    def getPack(self, args):
        """
        Download object and related information (attachment, media, people), join data 
        together and clean it.

        Expects 
        * args: a list with arguments that it passes along;
        * arg[0]: type (approval, exhibit or group)
        * arg[1]: id
        * arg[2]: label
        * arg[3]: attachments
        * arg[4]: since date, optional
        """
        print(f"GET PACK {args}")

        join_fn = self.join(args)
        self.getAttachments(args)

        cleanX = self.clean(args)  # takes too long
        # self.validate(path=join_fn) # doesn't validate b/c of bad uuid
        return cleanX

    def getPersons(self, args):
        return self._getPart(id=args[1], label=args[2], module="Person", type=args[0])

    def getRegistrar(self, args):
        return self._getPart(
            id=args[1], label=args[2], module="Registrar", type=args[0]
        )

    def join(self, args):
        type = args[0]
        id = args[1]
        label = args[2]
        try:
            since = args[4]
        except:
            since = None
        joinX = None
        join_fn = self.parts_dir.joinpath(
            f"{label}-join-{type}{id}.xml"
        )  # parts_dir now made during _mkdirs()

        if join_fn.exists():
            print(f" join from cache {join_fn}")
            joinX = self.xmlFromFile(path=join_fn)
        else:
            print(f" making new join from {join_fn}")

            # module for target and type refers to the type of selection
            pkX = self._getPart(module="Person", id=id, type=type, label=label, since=since)
            mmX = self._getPart(module="Multimedia", id=id, type=type, label=label, since=since)
            objX = self._getPart(module="Object", id=id, type=type, label=label, since=since)

            self.info(f" joining modules, saving to {join_fn}")
            inL = [objX, mmX, pkX]
            if type == "exhibit":
                exhX = self._getPart(module="Exhibition", id=id, type=type, label=label, since=since)
                regX = self._getPart(module="Registrar", id=id, type=type, label=label, since=since)
                inL.append(exhX)
                inL.append(regX)
            joinX = self.sar.join(inL=inL)
            self.xmlToFile(xml=joinX, path=join_fn)
        return join_fn

    def pack(self, args):
        """
        Pack (or join) all clean files into one bigger package. We act on all
        *-clean-*.xml files in the current project directory and save to
        $label$date.xml in current working directory.

        Seems to work, but needs too much memory. I will try saxon next.
        """
        label = str(self.project_dir.parent.name)
        date = str(self.project_dir.name)
        pack_fn = self.project_dir.joinpath(f"../{label}{date}.xml").resolve()
        if pack_fn.exists():
            print(f"Pack file exists already, no overwrite: {pack_fn}")
        else:
            print(f"Making new pack file: {pack_fn}")
            xmlL = list()
            for file in self.project_dir.glob("*-clean-*.xml"):
                print(f"Packing file {file}")
                xml = self.sar.xmlFromFile(path=file)
                xmlL.append(xml)
            xml = self.sar.join(inL=xmlL)
            self.sar.toFile(xml=xml, path=str(pack_fn))

    #
    # PUBLIC AND PRIVATE HELPERS
    #

    def _init_log(self):
        now = datetime.datetime.now()
        log_fn = Path(self.project_dir).joinpath(now.strftime("%Y%m%d") + ".log")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="a",  # append now since we're starting a new folder
            # every day now anyways.
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )

    def _getPart(self, *, id, label, module, type, since):
        # type is either loc, exhibit or group
        fn = self.parts_dir.joinpath(f"{label}-{module}-{type}{id}.xml")
        if fn.exists():
            print(f" {module} from cache {fn}")
            return self.xmlFromFile(path=fn)
        else:
            self.info(f" {module} from remote, saving to {fn}")
            if type == "approval":
                r = self.sar.getByApprovalGrp(id=id, module=module, since=since)
            elif type == "exhibit":
                r = self.sar.getByExhibit(id=id, module=module, since=since)
            elif type == "group":
                r = self.sar.getByGroup(id=id, module=module, since=since)
            elif type == "loc":
                r = self.sar.getByLocation(id=id, module=module, since=since)
            else:
                raise TypeError("UNKNOWN type")
            self.xmlToFile(xml=r.text, path=fn)
            return r.text

    def _mkdirs(self):
        date = datetime.datetime.today().strftime("%Y%m%d")
        dir = Path(self.job).joinpath(date)
        if not Path.is_dir(dir):
            Path.mkdir(dir, parents=True)
        self.project_dir = dir
        self.pix_dir = dir.parent.joinpath("pix")
        self.parts_dir = self.project_dir.joinpath("parts")
        if not self.parts_dir.exists():
            self.parts_dir.mkdir(parents=True)

    def etreeFromFile(self, *, path):
        return etree.parse(str(path), ETparser)

    def etreeToFile(self, *, ET, path):
        ET.write(
            str(path), pretty_print=True, xml_declaration=True, encoding="UTF-8"
        )  # encoding is important!

    def etreePrint(self, *, ET):
        print(etree.tostring(ET, pretty_print=True))

    def info(self, msg):
        logging.info(msg)
        print(msg)

    def validate(self, *, path):
        m = Module(file=path)
        print(" start validation ...")
        m.validate()
        print("OK")

    def xmlFromFile(self, *, path):
        # print (f"PATH {path}")
        with open(path, "r", encoding="utf8") as f:
            xml = f.read()
        return xml

    def xmlToEtree(self, *, xml):
        tree = etree.fromstring(bytes(xml, "utf-8"), ETparser)  # unicode
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


if __name__ == "__main__":
    import argparse

    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run", required=True)
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()

    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)

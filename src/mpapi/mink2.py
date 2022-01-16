"""
mink2.py: Commandline frontend for MpApi.py

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

DSL COMMANDs
    all     : chain together several jobs
    chunk   : paginted version of getPack
    getItem : save a single item to disk
    getPack : for a single id, get multi-type info (Objects, Multimedia, Persons...)
    pack    : pack together several clean files (todo: join)

    Usually called from inside chunk and getPack:
    getAttachments: downloads attachments for given module data
    join    : reads parts, joins and cleans them and writes join-file

MPAPI CLASSES
    SEARCH -> CLIENT -> MODULE
    SEARCH ->  SAR   -> MODULE
    mink: user interface, writes files

    search  : makes query objects
    client  : low-level client
    sar     : specialized higher level client
    module  : response data
    mink2   : CLI frontend

New
* Experimenting with sar2 for a cleaner interface. 20220116
* I eliminated some DSL commands that I haven't been using and integrated clean into join 20220116
* TODO: getPack ends now with a cleaned join file, so programs that expect clean file need to change
"""

import datetime
import logging
from lxml import etree  # necessary?
import os
from pathlib import Path
import requests
import sys

from mpapi.chunky import Chunky
from mpapi.module import Module
from mpapi.sar2 import Sar2
from mpapi.client import MpApi
from mpapi.search import Search

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Mink:
    def __init__(self, *, conf, job, baseURL, user, pw):
        self.sar = Sar2(baseURL=baseURL, user=user, pw=pw)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.chunker = Chunky(chunkSize=1000, baseURL=baseURL, pw=pw, user=user)
        self.conf = conf
        self._parse_conf(job=job)

    def _parse_conf(self, *, job):
        self.job = job
        self.current_job = None  # definition in conf file
        cmd = []
        args = []
        any_job = False
        # pretty ugly dsl parser...
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
                    raise TypeError("Too many indents in dsl file")

        if any_job is False:
            print(
                f"WARNING: User-supplied job didn't match any job from the definition file!"
            )

    #
    # HELPERS
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

    def _getPart(self, *, Id, label, module, Type, since=None) -> Module:
        """
        Gets a set of moduleItems depending on requested module type. Caches
        results in a file and returns from file cache if that exists already.

        Expects:
        * Type: query type (approval, exhibit, group or loc)
        * Id: Id of that query type
        * module: requested target module type
        * label: a label to be used as part of a filename (for cache)
        * since: dateTime (optional); if provided only get items newer than 
          that date

        Returns:
        * Module objct containing the data 
        """
        fn = self.parts_dir.joinpath(f"{label}-{module}-{Type}{Id}.xml")
        if fn.exists():
            print(f" {module} from cache {fn}")
            return Module(file=fn)
        else:
            self.info(f" {module} from remote, saving to {fn}")
            if type == "approval":
                m = self.sar.getByApprovalGrp(Id=Id, module=module, since=since)
            elif type == "exhibit":
                m = self.sar.getByExhibit(Id=Id, module=module, since=since)
            elif type == "group":
                m = self.sar.getByGroup(Id=Id, module=module, since=since)
            elif type == "loc":
                m = self.sar.getByLocation(Id=Id, module=module, since=since)
            else:
                raise TypeError("UNKNOWN type")
            m.toFile(path=fn)
            return m

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

    def info(self, msg):
        logging.info(msg)
        print(msg)

    #
    # MINK's DSL COMMANDs
    #

    def all(self, args):
        self._parse_conf(job=args[0])

    def chunk(self, args):
        """
        New chunky version of getPack

        Expects
        * args: a list with arguments that it passes along;
        * args[0]: type of the ID (approval, loc, exhibit or group)
        * args[1]: ID
        * args[2] (optional): since date

        * args[]: label (used for filename) -> not used ATM
        * args[]: attachments -> not implemented, not needed ATM

        NEW
        * I would like the ability to start where the last run stopped. To do
          so, we need to establish the last chunk on disk and its number and
          then calculate the offset.
          So three chunks got written, the fourth aborted, so offset
          would 3 x 1000
        """
        Type = args[0]
        ID = args[1]
        try:
            since = args[2]
        except:
            since = None

        print(
            f" CHUNKER: {Type}-{ID} since:{since} chunkSize: {self.chunker.chunkSize}"
        )
        no = 1

        path2 = self.project_dir.joinpath(f"{Type}{ID}-chunk{no}.xml")
        while path2.exists():
            path2 = self.project_dir.joinpath(f"{Type}{ID}-chunk{no}.xml")
            no += 1
        else:
            if no > 1:
                no -= 1

        offset = (no - 1) * self.chunker.chunkSize
        print(f" next chunk {no}; offset:{offset}")

        for chunk in self.chunker.getByType(
            ID=ID, Type=Type, since=since, offset=offset
        ):
            path = self.project_dir.joinpath(f"{Type}{ID}-chunk{no}.xml")
            chunk.clean()
            print(f"saving CLEAN to {path}")
            chunk.toFile(path=path)
            chunk.validate()
            no += 1


    def getAttachments(self, args):
        """
        Gets (downloads) attachments for module of certain types. Usually writes
        attachments to path as follows:
            pix_{label}/{mulId}.{ext}

        Currently, getAttachments relies on the file "{label}-Multimedia-{Type}{Id}.xml"
        for multimedia items. So make sure that this file exists (that getMedia has been
        called before).

        Expects:
        * arg: list with parameters
        * arg[0]: type (exhibit, group, approval or loc)
        * arg[1]: id of the respective type
        * arg[2]: label (used for filenames)
        * arg[3]: only if string "attachments", will d/l them (optional)
        * arg[4]: timestamp (optional); if specified, d/l attachents to subdir pix_update
        """

        # print(f"***{args}")
        Type = args[0]
        Id = args[1]
        label = args[2]
        try:
            since = args[4]
        except:
            since = None
        try:
            args[3]
        except:
            print(" not downloading attachments")
            att = None
        else:  # executed if no exceptions were raised in the try block.
            att = str(args[3]).lower().strip()

        if att == "attachments":
            # pretty dirty: assumes that getMedia has been done before
            mm_fn = self.parts_dir.joinpath(f"{label}-Multimedia-{Type}{Id}.xml")
            print(f" looking for multimedia info at {mm_fn}")
            mmM = Module(file=mm_fn)

            # determine target dir
            if since is None:
                pix_dir = Path(f"{self.pix_dir}_{label}")
            else:
                pix_dir = Path(f"{self.pix_dir}_update")
            if not pix_dir.exists():
                pix_dir.mkdir()
            print(f" about to check attachments; saving to {pix_dir}")

            try:
                expected = self.sar.saveAttachments(obj=mmM, adir=pix_dir, since=since)
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


    def getItem(self, args):
        """
        gets a single items. Caches item on disk at
            {project_dir}/{id}.xml
        and makes new http request only if cache doesn't exist.

        Expects
        * args: list with two arguments
        * args[0] module type
        * args[1] id

        returns
        * writes item to disk as side-effect
        """
        module = args[0]
        Id = args[1]
        out_fn = self.project_dir.joinpath(args[1] + ".xml")
        if out_fn.exists():
            print(f" Item from cache {out_fn}")
            return Module(file=out_fn)
        else:
            self.info(f"getItem module={module} Id={Id} out_fn={out_fn}")
            r = self.api.getItem(module=module, id=Id)
            m = Module(xml=r.text)
            m.toFile(path=out_fn)
            return m


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

        Returns
        * xml as string with a clean, zml document containing at least objects, persons
          and multimedia
        """
        print(f"GET PACK {args}")
        join_fn = self.join(args)  # write join file
        self.getAttachments(args)  # d/l attachments
        cleanM = self.clean(args)  # includes validation 
        return cleanM


    def join(self, args):
        Type = args[0]
        Id = args[1]
        label = args[2]
        try:
            since = args[4]
        except:
            since = None

        # parts_dir now made during _mkdirs()
        join_fn = self.parts_dir.joinpath(
            f"{label}-join-{Type}{Id}.xml"
        )  

        if join_fn.exists():
            print(f" join from cache {join_fn}")
            m = Module(file=join_fn)
        else:
            self.info(f" joining modules, saving to {join_fn}")

            # module for target and type refers to the type of selection
            m = self._getPart(
                module="Person", Id=Id, Type=Type, label=label, since=since
            ) + self._getPart(
                module="Multimedia", Id=Id, Type=Type, label=label, since=since
            ) + self._getPart(
                module="Object", Id=Id, Type=Type, label=label, since=since
            )

            if Type == "exhibit":
                m = m + self._getPart(
                    module="Exhibition", Id=Id, Type=Type, label=label, since=since
                ) + self._getPart(
                    module="Registrar", Id=Id, Type=Type, label=label, since=since
                )
            m.clean()
            m.validate()
            m.toFile(path=join_fn)
        return join_fn


    def pack(self, args):
        """
        Pack (or join) all clean files into one bigger package. We act on all
        *-clean-*.xml files in the current project directory and save to
        $label$date.xml in current working directory.

        TODO: clean file has been eliminated. Change the input
        """
        label = str(self.project_dir.parent.name)
        date = str(self.project_dir.name)
        pack_fn = self.project_dir.joinpath(f"../{label}{date}.xml").resolve()
        if pack_fn.exists():
            print(f"Pack file exists already, no overwrite: {pack_fn}")
        else:
            print(f"Making new pack file: {pack_fn}")
            m = Module()
            for in_fn in self.project_dir.glob("*-join-*.xml"):
                print(f"Packing file {in_fn}")
                m = m + Module(file=in_fn)
            m.toFile(path=str(pack_fn))


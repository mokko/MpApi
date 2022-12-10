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

DSL COMMANDs
    all     : chain together several jobs
    chunk   : paginated version of getPack
    getItem : save a single item to disk
    getPack : for a single id, get multi-type info (Objects, Multimedia, Persons...)
    pack    : pack together several (clean) files
    getAttachments: downloads attachments for given module data

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
* 20221210: use separate command getAttachments to d/l attachments 
"""

import datetime
import logging
from lxml import etree  # necessary?
import os
from pathlib import Path
import requests
import sys
from typing import NewType, Optional, Union

from mpapi.chunky import Chunky
from mpapi.client import MpApi
from mpapi.module import Module
from mpapi.sar import Sar
from mpapi.search import Search

Since = Optional[str]

ETparser = etree.XMLParser(remove_blank_text=True)
NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

allowed_commands = ["all", "chunk", "getItem", "getPack", "pack"]


class Mink:
    def __init__(
        self, *, conf: str, job: str, baseURL: str, user: str, pw: str
    ) -> None:
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.chunker = Chunky(chunkSize=1000, baseURL=baseURL, pw=pw, user=user)
        self.conf = conf
        self._parse_conf(job=job)

    def _parse_conf(self, *, job: str) -> None:
        """
        For a job specified on command line, executes the dsl commands in that job.
        """
        self.job = job  # job requested to execute from command line
        self.current_job = None  # definition in conf file
        args: list = []
        any_job: bool = False
        # pretty ugly dsl parser...
        with open(self.conf, mode="r") as file:
            c = 0  # line counter
            for line in file:
                c += 1
                uncomment = line.split("#", 1)[0].strip()
                if uncomment.isspace() or not uncomment:
                    continue
                line = line.expandtabs(4)
                indent_lvl = int((len(line) - len(line.lstrip()) + 4) / 4)
                parts: list[str] = uncomment.split()
                if indent_lvl == 1:  # job label
                    if not parts[0].endswith(":"):
                        raise SyntaxError(
                            f"Job label has to end with colon: line {c} {parts[0]}"
                        )
                    self.current_job = parts[0][:-1]
                    if self.current_job == job:
                        right_job = True
                        any_job = True
                        self._mkdirs()  # also sets project_dir etc.
                        self._init_log()
                        self.info(f"Project dir: {self.project_dir}")
                    else:
                        self.project_dir: Path = Path(".")
                        right_job = False
                    continue
                elif indent_lvl == 2:
                    cmd: str = parts[0]
                    if len(parts) > 1:
                        args = parts[1:]
                    else:
                        args = []
                    if right_job is True:
                        # print(f"**{cmd} {args}")
                        if cmd in allowed_commands:
                            getattr(self, cmd)(args)
                        else:
                            raise SyntaxError(f"ERROR: Command {cmd} not recogized")
                elif indent_lvl > 2:
                    print(f"indent lvl: {indent_lvl} {parts}")
                    raise SyntaxError("ERROR: Too many indents in dsl file")

        if any_job is False:
            print(
                f"WARNING: User-supplied job didn't match any job from the definition file!"
            )

    #
    # HELPERS
    #

    def _init_log(self) -> None:
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

    def _getPart(
        self, *, Id: int, label: str, module: str, Type: str, since: str = None
    ) -> Module:
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
        fn = self.parts_dir / f"{label}-{module}-{Type}{Id}.xml"
        if fn.exists():
            print(f" {module} from cache {fn}")
            return Module(file=fn)
        else:
            # print (f"GH TYPE {Type}")
            self.info(f" {module} from remote, saving to {fn}")
            if Type == "approval":
                m = self.sar.getByApprovalGrp(Id=Id, module=module, since=since)
            elif Type == "exhibit":
                # print ("***GH Exhibit")
                m = self.sar.getByExhibit(Id=Id, module=module, since=since)
            elif Type == "group":
                m = self.sar.getByGroup(Id=Id, module=module, since=since)
            elif Type == "loc":
                m = self.sar.getByLocation(Id=Id, module=module, since=since)
            else:
                raise TypeError("UNKNOWN type")
            m.toFile(path=fn)
            return m

    def _mkdirs(self) -> None:
        date: str = datetime.datetime.today().strftime("%Y%m%d")
        adir: Path = Path(self.job) / date
        if not adir.is_dir():
            Path.mkdir(adir, parents=True)
        self.project_dir = adir
        self.pix_dir = adir.parent / "pix"
        # We dont need parts dir when in chunk mode
        self.parts_dir = self.project_dir / "parts"

    def info(self, msg: str) -> None:
        logging.info(msg)
        print(msg)

    #
    # MINK's DSL COMMANDs
    #

    def all(self, args: list) -> None:
        self._parse_conf(job=args[0])

    def chunk(self, args: list) -> None:
        """
        New chunky version of getPack

        Expects
        * args: a list with arguments that it passes along;
        * args[0]: type of the ID (approval, exhibit, group, loc, query)
        * args[1]: ID
        * args[2]: target type (new, only optional when args[3] and args[4} are not used)
        * args[3]: attachment (optional, only optional if args[4] is not used)
        * args[4]: since date (optional)

        NEW
        * If last run was aborted, you can restart where you left off, so exisiting chunks
          are not downloaded again. Target is only actually needed for savedQueries.
        * You can use queries that target something else than objects
        """
        Type: str = args[0]
        ID: int = args[1]
        try:
            target: str = args[2]
        except:
            target: str = "Object"  # default value
        try:
            attachment = args[3]
        except:
            attachment = None
        try:
            since: Since = args[4]
        except:
            since = None

        print(
            f" CHUNKER: {Type}-{ID} since:{since} chunkSize: {self.chunker.chunkSize} "
        )
        no = 1

        path2 = self.project_dir / f"{Type}{ID}-chunk{no}.xml"
        while path2.exists():
            path2 = self.project_dir / f"{Type}{ID}-chunk{no}.xml"
            no += 1
        else:
            if no > 1:
                no -= 1

        offset = (no - 1) * self.chunker.chunkSize
        # print(f" next chunk {no}; offset:{offset}")

        # getByType returns Module, not ET
        for chunk in self.chunker.getByType(
            ID=ID,
            Type=Type,
            target=target,
            since=since,
            offset=offset,
            attachment=attachment,
        ):
            if chunk:  # Module is true if it has more than 0 items
                path = self.project_dir / f"{Type}{ID}-chunk{no}.xml"
                chunk.clean()
                print(f"saving chunk {path}")
                chunk.toFile(path=path)
                chunk.validate()
            no += 1

    def getAttachments(self, args: list) -> None:
        """
        Gets (downloads) attachments for module of certain types. Usually writes
        attachments to path as follows:
            pix_{label}/{mulId}.{ext}

        Currently, getAttachments relies on the file "{label}-Multimedia-{Type}{Id}.xml"
        for Multimedia items. So make sure that this file exists (that getMedia has been
        called before).

        Expects:
        * arg: list with parameters
        * arg[0]: type (approval, exhibit, group or loc)
        * arg[1]: id of the respective type
        * arg[2]: label (used for filenames)
        * arg[3]: timestamp (optional); if specified, d/l attachents to subdir pix_update
        """

        # print(f"***{args}")
        Type = args[0]
        Id = args[1]
        label = args[2]
        try:
            since = args[3]
        except:
            since = None

        # pretty dirty: assumes that getMedia has been done before
        mm_fn = self.parts_dir / f"{label}-Multimedia-{Type}{Id}.xml"
        print(f" looking for Multimedia info at {mm_fn}")

        # determine target dir
        if since is None:
            pix_dir = Path(f"{self.pix_dir}_{label}")
        else:
            pix_dir = Path(f"{self.pix_dir}_update")
        if not pix_dir.exists():
            pix_dir.mkdir()
        print(f" about to check attachments; saving to {pix_dir}")

        mm = Module(file=mm_fn)
        try:
            expected = self.sar.saveAttachments(data=mm, adir=pix_dir, since=since)
        except Exception as e:
            self.info("Error during saveAttachments")
            raise e

            # do we want to delete those files that are no longer attached?
            # for img in os.listdir(pix_dir):
            #    img = pix_dir.joinpath(img)  # need resolve here
            #    if img not in expected:
            #        print(f"image no longer attached, removing {img}")
            #        os.remove(img)
        # currently we dont get attachments that have changed, but keep the same mulId,
        # that case should be rare

    def getItem(self, args: list) -> Module:
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
        out_fn = self.project_dir / args[1] + ".xml"
        if out_fn.exists():
            print(f" Item from cache {out_fn}")
            return Module(file=out_fn)
        else:
            self.info(f"getItem module={module} Id={Id} out_fn={out_fn}")
            r = self.api.getItem(module=module, id=Id)
            m = Module(xml=r.text)
            m.toFile(path=out_fn)
            return m

    def getPack(self, args: list) -> None:
        """
        Download object and related information (attachment, media, people), join data
        together and clean it.

        Expects
        * args: a list with arguments that it passes along;
        * arg[0]: type (approval, exhibit or group)
        * arg[1]: id
        * arg[2]: label
        * arg[3]: since date, optional

        Returns
        * None
        """
        print(f"GET PACK {args}")
        join_fn = self.join(args)  # write join file, includes validation
        # if we need to return M, we need to load it from join_fn

    def join(self, args: list) -> Path:
        Type = args[0]
        Id = args[1]
        label = args[2]
        try:
            since = args[4]
        except:
            since = None

        # let's only make parts dir if we need it...
        if not self.parts_dir.exists():
            self.parts_dir.mkdir(parents=True)

        # parts_dir now made during _mkdirs()
        join_fn = self.project_dir / f"{label}-join-{Type}{Id}.xml"

        if join_fn.exists():
            print(f" join from cache {join_fn}")
            m = Module(file=join_fn)
        else:
            self.info(f" joining modules, saving to {join_fn}")

            # module for target and type refers to the type of selection
            m = (
                self._getPart(
                    module="Person", Id=Id, Type=Type, label=label, since=since
                )
                + self._getPart(
                    module="Multimedia", Id=Id, Type=Type, label=label, since=since
                )
                + self._getPart(
                    module="Object", Id=Id, Type=Type, label=label, since=since
                )
            )

            if Type == "exhibit":
                print(" d: about to get exhibit...")
                m += self._getPart(
                    module="Exhibition", Id=Id, Type=Type, label=label, since=since
                ) + self._getPart(
                    module="Registrar", Id=Id, Type=Type, label=label, since=since
                )
            print(" d: start cleaning")
            m.clean()
            m.validate()
            m.toFile(path=join_fn)
        return join_fn

    def pack(self, args: list) -> None:
        """
        Pack (or join) all clean files into one bigger package. We act on all
        *-join-*.xml files in the current project directory and save to
        $label$date.xml in current working directory.

        TODO: clean file has been eliminated. Change the input
        """
        label = str(self.project_dir.parent.name)
        date = str(self.project_dir.name)
        pack_fn = self.project_dir / f"../{label}{date}.xml".resolve()
        if pack_fn.exists():
            print(f"Pack file exists already, no overwrite: {pack_fn}")
        else:
            print(f"Making new pack file: {pack_fn}")
            m = Module()
            for in_fn in self.project_dir.glob("*-join-*.xml"):
                print(f"Packing file {in_fn}")
                m = m + Module(file=in_fn)
            m.toFile(path=pack_fn)

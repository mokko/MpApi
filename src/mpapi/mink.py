"""
mink.py: Commandline frontend for MpApi; dowloads native xml & writes files

CLI USAGE
    cd projectData
    mink.py -j job

CONFIGURATION
    $HOME/RIA.toml           # credentials
    jobs.toml                # defines multiple jobs; expected above project dir

DIR STRUCTURE
    projectData              # <-- use it as working directory (pwd)
        ajob/20210401        # <-- project dir, created by running mink
        jobs.toml             # expected in pwd

COMMANDs (from jobs.toml)
    chunk   : paginated version of getPack
    getItem : save a single item to disk
    getPack : for a single id, get multi-type info (Objects, Multimedia, Persons...)
    pack    : pack together several (clean) files
"""

import datetime
import logging
from mpapi.chunky import Chunky
from mpapi.client import MpApi
from mpapi.constants import load_conf
from mpapi.module import Module
from mpapi.sar import Sar
from pathlib import Path
import sys
from typing import Optional


chunkSize = 1000


class Mink:
    def __init__(
        self, *, conf: str, job: str, baseURL: str, user: str, pw: str
    ) -> None:
        # if you can't load jobs.toml, we're likely in wrong diretory
        self.job_data = self._parse_conf(job=job, fn=Path(conf))
        self.project_dir = self._mkdirs(job)
        self.parts_dir = self.project_dir / "parts"
        self._init_log(self.project_dir)
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.chunker = Chunky(chunkSize=chunkSize, baseURL=baseURL, pw=pw, user=user)
        logging.info(f"Project dir: {self.project_dir}")

        Type = self.job_data["type"]  # cannot be None
        ID = self.job_data["id"]
        label = self._init_conf_value("label")  # can be None
        since = self._init_conf_value("since")
        # target = self._init_conf_value("target")

        match self.job_data["cmd"]:
            case "chunk":
                onlyPublished = False
                try:
                    self.job_data["onlyPublished"]
                except KeyError:
                    pass
                else:
                    if self.job_data["onlyPublished"].lower() == "true":
                        onlyPublished = True
                self.chunk(
                    Type=Type,
                    ID=ID,
                    since=since,
                    target="Object",
                    onlyPublished=onlyPublished,
                )
            case "getItem":
                self.getItem(module=Type, ID=ID)
            case "getPack":
                self.getPack(Type=Type, ID=ID, since=since, label=label)
            case "join":
                self.join(Type=Type, ID=ID, since=since, label=label)
            case "pack":  # untested
                self.pack()

    def chunk(
        self,
        Type: str,
        ID: int,
        target: Optional[str] = "Object",
        since: Optional[str] = None,
        onlyPublished: bool = False,
    ) -> None:
        """
        New chunky version of getPack

        NEW
        * If last run was aborted, you can restart where you left off, so exisiting chunks
          are not downloaded again. Target is only actually needed for savedQueries.
        * You can use queries that target something else than objects
        """
        print(
            f" CHUNKER: {Type}-{ID} since:{since} chunkSize: {self.chunker.chunkSize} "
        )

        # ignore chunks already on disk
        no, offset = self._fastforward(Type=Type, ID=ID, suffix=".zip")
        print(f" fast forwarded to chunk no {no} with offset {offset}")
        # how can i know if this is the last chunk?
        # Test if the last chunk has less items than chunkSize OR
        # Do another request to RIA and see if it comes back empty?
        # we go the second route

        # getByType returns Module, not ET
        for chunk in self.chunker.getByType(
            ID=ID,
            Type=Type,
            target=target,
            since=since,
            offset=offset,
            onlyPublished=onlyPublished,
        ):
            if chunk:  # Module is True if >0 items
                # print(f"###chunk size:{chunk.actualSize(module='Object')}")
                chunk_fn = self._chunkPath(Type=Type, ID=ID, no=no, suffix=".xml")
                chunk.clean()
                logging.info(f"zipping chunk {chunk_fn}")
                chunk.toZip(path=chunk_fn)
                chunk.validate()
                no += 1
            else:
                print("Chunk empty; we're at the end")

    def getItem(self, module: str, ID: int) -> Module:
        """
        gets a single item and caches it on disk at
            {project_dir}/getItem-{module}-{ID}.xml

        Makes new http request only if cache doesn't exist. So you might need to delete
        cache file manually.
        """
        out_fn = self.project_dir / f"getItem-{module}-{ID}.xml"
        if out_fn.exists():
            print(f" Item from cache {out_fn}")
            return Module(file=out_fn)
        else:
            logging.info(f"getItem module={module} Id={ID} out_fn={out_fn}")
            r = self.api.getItem(module=module, id=ID)
            m = Module(xml=r.text)
            m.toFile(path=out_fn)
            return m

    def getPack(
        self,
        Type: str,
        ID: int,
        label: Optional[str] = None,
        since: Optional[str] = None,
    ) -> None:
        """
        Download object and related information (attachment, media, people), join,
        validate and clean it.
        """
        if label is None:
            label = ""
        print(f"GET PACK {Type=} {ID=} {label=} {since=}")
        self.join(
            Type=Type, ID=ID, label=label, since=since
        )  # write join file, includes validation

    def join(
        self, Type: str, ID: int, label: Optional[str], since: Optional[str] = None
    ) -> Path:
        if label is None:
            label = ""

        if not self.parts_dir.exists():
            self.parts_dir.mkdir(parents=True)

        # parts_dir now made during _mkdirs()
        join_fn = self.project_dir / f"{label}-join-{Type}{ID}.xml"

        if join_fn.exists():
            print(f" join from cache {join_fn}")
            m = Module(file=join_fn)
        else:
            logging.info(f" joining modules, saving to {join_fn}")

            # module for target and type refers to the type of selection
            m = (
                self._getPart(
                    module="Person", Id=ID, Type=Type, label=label, since=since
                )
                + self._getPart(
                    module="Multimedia", Id=ID, Type=Type, label=label, since=since
                )
                + self._getPart(
                    module="Object", Id=ID, Type=Type, label=label, since=since
                )
            )

            if Type == "exhibit":
                print(" d: about to get exhibit...")
                m += self._getPart(
                    module="Exhibition", Id=ID, Type=Type, label=label, since=since
                ) + self._getPart(
                    module="Registrar", Id=ID, Type=Type, label=label, since=since
                )
            print(" d: start cleaning")
            m.clean()
            m.validate()
            m.toFile(path=join_fn)
        return join_fn

    def pack(self) -> None:
        """
        Pack (or join) all clean files into one bigger package. We act on all
        *-join-*.xml files in the current project directory and save to
        $label$date.xml in current working directory.
        """
        label = str(self.project_dir.parent.name)
        date = str(self.project_dir.name)
        pack_fn = self.project_dir.parent / f"{label}{date}.xml"
        if pack_fn.exists():
            print(f"Pack file exists already, no overwrite: {pack_fn}")
        else:
            print(f"Making new pack file: {pack_fn}")
            m = Module()
            for in_fn in self.project_dir.glob("*-join-*.xml"):
                print(f"Packing file {in_fn}")
                m = m + Module(file=in_fn)
            m.toFile(path=pack_fn)

    #
    # HELPERS
    #

    def _chunkPath(self, *, Type, ID, no, suffix):
        return self.project_dir / f"{Type}{ID}-chunk{no}{suffix}"

    def _fastforward(self, *, Type, ID, suffix):
        """
        Given the usual params for a chunk filename (i.e. Type,ID, suffix), we loop
        thru existing chunk files and return number of the last existing chunk file as
        well as the corresponding offset.
        """
        no = 1
        while (self._chunkPath(Type=Type, ID=ID, no=no, suffix=suffix)).exists():
            no += 1
        else:
            if no > 1:
                no -= 1

        offset = (no - 1) * self.chunker.chunkSize
        return no, offset
        # print(f" next chunk {no}; offset:{offset}")

    def _getPart(
        self,
        *,
        Id: int,
        label: str,
        module: str,
        Type: str,
        since: Optional[str] = None,
    ) -> Module:
        """
        Gets a set of moduleItems depending on requested module type. Caches
        results in a file and returns from file cache if that exists already.

        Type: query type (approval, exhibit, group or loc)
        """
        fn = self.parts_dir / f"{label}-{module}-{Type}{Id}.xml"
        if fn.exists():
            print(f" {module} from cache {fn}")
            return Module(file=fn)
        else:
            # print (f"GH TYPE {Type}")
            logging.info(f" {module} from remote, saving to {fn}")
            match Type:
                case "approval":
                    m = self.sar.getByApprovalGrp(Id=Id, module=module, since=since)
                case "exhibit":
                    # print ("***GH Exhibit")
                    m = self.sar.getByExhibit(Id=Id, module=module, since=since)
                case "group":
                    m = self.sar.getByGroup(Id=Id, module=module, since=since)
                case "loc":
                    m = self.sar.getByLocation(Id=Id, module=module, since=since)
                case _:
                    raise TypeError("UNKNOWN type")
            m.toFile(path=fn)
            return m

    def _init_conf_value(self, key):
        """
        Return conf value by key or None if value doesn't exist
        """
        try:
            value = self.job_data[key]
        except KeyError:
            value = None
        return value

    def _init_log(self, project_dir: Path) -> None:
        now = datetime.datetime.now()
        log_fn = Path(project_dir).joinpath(now.strftime("%Y%m%d") + ".log")
        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="a",  # append now since we're starting a new folder
            # every day now anyways.
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )
        log = logging.getLogger()
        log.addHandler(logging.StreamHandler(sys.stdout))

    def _mkdirs(self, job: str) -> Path:
        """
        Determine, make and return project directory.
        It has this shape "job_name/20240609" and will be created in current dir.
        """
        date: str = datetime.datetime.today().strftime("%Y%m%d")
        project_dir = Path(job) / date
        if not project_dir.is_dir():
            Path.mkdir(project_dir, parents=True)
        return project_dir

    def _parse_conf(self, job: str, fn: Path) -> dict:
        """
        Load configuration file, check for required keys and return info for current job.
        """
        try:
            conf_data = load_conf(fn)
        except FileNotFoundError:
            raise FileNotFoundError(
                "File jobs.toml not found in this dir. Are you in the right dir?"
            )

        try:
            job_data = conf_data[job]
        except KeyError:
            raise SyntaxError(f"Job '{job}' not known in configuration")

        for key in ["cmd", "type", "id"]:
            try:
                job_data[key]
            except KeyError:
                raise SyntaxError("job '{job}' missing config value '{key}'")
        return job_data


if __name__ == "__main__":
    # since fvh is blocked by Windows group policy
    import argparse
    from mpapi.constants import get_credentials

    user, pw, baseURL = get_credentials()

    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")  # , required=True
    parser.add_argument("-c", "--conf", help="config file", default="jobs.toml")
    parser.add_argument(
        "-v", "--version", help="Display version information", action="store_true"
    )
    args = parser.parse_args()
    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)
    Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)

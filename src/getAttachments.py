"""
getAttachments downloads attachments from RIA

Configuration file format (where | indicates the possible options):
#file is typically named 'getAttachments.jobs'
[label]
    type: group | exhibit | loc | restExhibit
    id: 12345
    restriction: None | freigegeben
    name: dateiname | mulid

You also need the credentials.py file in the pwd.

    getAttachments -j label

will put attachments in dir 
    ./label/20220708
where the current date is used for the second directory.
"""

import argparse
import configparser
from datetime import date
from mpapi.client import MpApi
from mpapi.constants import get_credentials
from mpapi.module import Module
from mpapi.search import Search
from pathlib import Path

conf_fn = "getAttachments.jobs"
response_cache = "_ga_response.xml"  # cache
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}


def get_attachment(c: MpApi, ID: int) -> None:
    """
    Get attachment from a specified Multimedia ID and save to disk. There can be only
    one or none attachment.

    This function profits from its more recent inception. Uses underscore in name,
    function instead of method, no keyword argument.
    """

    print(f"Getting Multimedia {ID}")
    # we need the dateiname to save, assuming there can be only one.
    m = c.getItem2(mtype="Multimedia", ID=ID)
    # m.toFile(path=f"debug.multimedia{ID}")
    if (
        m.xpath("/m:application/m:modules/m:module/m:moduleItem/@hasAttachments")[0]
        == "true"
    ):
        hasAttachments = True
    else:
        hasAttachments = False
        raise ValueError("ERROR: Record has no attachment")

    try:
        fn = m.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/m:dataField[@name='MulOriginalFileTxt']/m:value/text()"
        )[0]
    except:
        fn = f"{ID}.jpg"  # use mulId as a fallback if no dateiname in RIA
        print("WARNING: Falling back to {fn} since no Dateiname specified in RIA")

    print(f"About to save attachment to '{fn}'")
    c.saveAttachment(id=ID, path=fn)


class GetAttachments:
    def __init__(self, *, job: str, cache: bool = False) -> None:
        user, pw, baseURL = get_credentials()
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.job = job
        self.conf = self.setup_conf()

        if cache:
            print("* loading cached response")
            m = Module(file=response_cache)
        else:
            print(f"* launching new search")
            m = self.query()
            m.toFile(path=response_cache)

        self.process_response(data=m)

    def process_response(self, *, data: Module) -> None:
        print(f"* processing response")
        no = data.actualSize(module="Multimedia")
        print(f"* {no} digital assets found")

        yyyymmdd = date.today().strftime("%Y%m%d")
        out_dir = Path(self.job) / yyyymmdd

        if not out_dir.exists():
            print(f"* Making dir {out_dir}")
            out_dir.mkdir(parents=True)

        print(f"* response has {no} asset items")

        for item in data.iter(module="Multimedia"):
            ID = item.get("id")
            if item.get("hasAttachments") == "true":
                hasAttachments = True
            else:
                hasAttachments = False

            try:
                dateiname = item.xpath(
                    "./m:dataField[@name='MulOriginalFileTxt']/m:value/text()",
                    namespaces=NSMAP,
                )[0]
            except:
                dateiname = (
                    f"{ID}.jpg"  # use mulId as a fallback if no dateiname in RIA
                )
                # there is a chance that this file is no jpg
                print(
                    f"WARNING: Falling back to ID {dateiname} since no Dateiname specified in RIA"
                )
            print(f"*  mulId {ID}")  # {dateiname}
            match self.conf["name"]:
                case "mulId":
                    suffix = Path(dateiname).suffix
                    path = out_dir / f"{ID}{suffix}"
                case "dateiname":
                    path = out_dir / dateiname
                case _:
                    raise SyntaxError(
                        f"Error: Unknown config value: {self.conf['name']}"
                    )

            if hasAttachments:  # only d/l if there is an attachment
                if path.exists():  # let's not overwrite existing files
                    print("\tfile exists already")
                else:
                    print(f"\t{path}")
                    self.api.saveAttachment(id=ID, path=path)
            else:
                print("\tno attachment")

    def query(self) -> Search:
        """
        Restriction: Currently, only gets attachments from Multimedia.
        """
        qu = Search(module="Multimedia")
        if self.conf["restriction"] == "freigegeben":
            qu.AND()

        self._qm_type(query=qu, Id=self.conf["id"])

        match self.conf["restriction"]:
            case "freigegeben":
                qu.addCriterion(
                    operator="equalsField",
                    field="MulApprovalGrp.TypeVoc",
                    value="1816002",  # SMB-Digital; search wants str
                )
                qu.addCriterion(
                    operator="equalsField",
                    field="MulApprovalGrp.ApprovalVoc",
                    value="4160027",  # Ja
                )
        qu.addField(field="MulOriginalFileTxt")  # speeds up query a lot!
        qu.validate(mode="search")
        print(f"* about to execute query\n{qu.toString()}")
        return self.api.search2(query=qu)

    def setup_conf(self) -> dict:
        """
        Returns configuration for selected job
        """
        config = configparser.ConfigParser()
        required = ["type", "id", "restriction", "name"]
        if not Path(conf_fn).exists():
            raise SyntaxError(f"ERROR: conf file not found! {conf_fn}")
        config.read(conf_fn)
        print(f"* Using job '{self.job}' from {conf_fn}")
        try:
            c = config[self.job]
        except:
            raise SyntaxError(f"job '{self.job}' not found")

        for each in required:
            try:
                c[each]
            except:
                raise SyntaxError(f"Config value {each} missing!")

        print(f"   type: {c['type']}")
        print(f"   id: {c['id']}")
        print(f"   rest: {c['restriction']}")
        print(f"   name: {c['name']}")
        return c

    #
    #
    #

    def _qm_type(self, *, query: Search, Id: int):
        match self.conf["type"]:
            case "approval":
                raise SyntaxError("ERROR: approval group mode not implemented yet!")
            case "exhibit":
                query.addCriterion(  #  get assets attached to objects in a given exhibition
                    operator="equalsField",
                    field="MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
                    value=Id,
                )
            case "group":
                query.addCriterion(  #  get assets attached to objects in a given group
                    operator="equalsField",
                    field="MulObjectRef.ObjObjectGroupsRef.__id",
                    value=Id,
                )
            case "loc":
                print("WARN: location mode not tested yet!")
                qu.addCriterion(  #  get assets attached to objects at a given location
                    operator="equalsField",
                    field="MulObjectRef.ObjCurrentLocationVoc",
                    value=Id,
                )
            case "restExhibit":
                # get assets attached to restauration records attached to an exhibit
                # photos are typically not SMB-approved
                query.addCriterion(
                    operator="equalsField",
                    field="MulConservationRef.ConExhibitionRef.__id",
                    value=Id,
                )
            case _:
                raise TypeError(f"ERROR: Unknown type! {self.conf['type']}")

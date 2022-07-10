"""
getAttachments from RIA

Command line client to download attachments from RIA groups.
    getAttachments -j Hauke 
will put attachments in dir ./Hauke/20220708

Two configuration files are needed 
- credentials.py (in pwd)
- getAttachments.jobs (in pwd, using normal config format)
Hauke:
    type: group
    id: 12345
    restriction: None | freigegeben
    name: dateiname| mulid
"""

import argparse
import configparser
from datetime import date
from mpapi.client import MpApi
from mpapi.module import Module
from mpapi.search import Search
from pathlib import Path

conf_fn = "getAttachments.jobs"
credentials = "credentials.py"  # expect credentials in pwd
response_cache = "_ga_response.xml"  # for debugging purposes
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}

if Path(credentials).exists():
    with open(credentials) as f:
        exec(f.read())


class GetAttachments:
    def __init__(self, *, baseURL: str, job: str, user: str, pw: str) -> None:
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.job = job
        self.setup_conf()

        if Path(response_cache).exists():
            print(f"* loading response cache from '{response_cache}'")
            m = Module(file=response_cache)
        else:
            print(
                f"* launching new query; will write response cache to '{response_cache}'"
            )
            m = self.query()
            m.toFile(path=response_cache)  # debug

        self.process_response(data=m)

    def process_response(self, *, data):
        no = data.actualSize(module="Multimedia")
        name_policy = self.conf["name"]
        print(f"* {no} digital assets found")

        yyyymmdd = date.today().strftime("%Y%m%d")
        out_dir = Path(self.job).joinpath(yyyymmdd)

        if not out_dir.exists():
            print(f"* Making dir {out_dir}")
            out_dir.mkdir(parents=True)

        print(f"* response has {len(data)} asset items")

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
            print(f"*  mulId {ID} {hasAttachments}")  # {dateiname}
            if name_policy == "mulId":
                ext = Path(dateiname).suffix
                path = out_dir.joinpath(f"{ID}{ext}")
            elif name_policy == "dateiname":
                path = out_dir.joinpath(dateiname)
            else:
                raise SyntaxError(f"Error: Unknown config value: {name_policy}")

            if hasAttachments:  # only d/l if there is an attachment
                if path.exists():  # let's not overwrite existing files
                    print("\tfile exists already")
                else:
                    print(f"\t{path}")
                    self.api.saveAttachment(id=ID, path=path)
            else:
                print("\tno attachment")

    def query(self):
        print(f"* type: {self.conf['type']}")
        print(f"* id: {self.conf['id']}")  # id is group id
        qu = Search(module="Multimedia")
        if self.conf["type"] == "group":
            # should get all assets of the objects in the given group
            if self.conf["restriction"] == "freigegeben":
                qu.AND()
            qu.addCriterion(
                operator="equalsField",
                field="MulObjectRef.ObjObjectGroupsRef.__id",
                value=self.conf["id"],
            )
            if self.conf["restriction"] == "freigegeben":
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
        else:
            raise TypeError(f"ERROR: This type is not known! {self.conf['type']}")

    def setup_conf(self):
        config = configparser.ConfigParser()
        if not Path(conf_fn).exists():
            raise SyntaxError(f"ERROR: conf file not found! {conf_fn}")
        config.read(conf_fn)
        print(f"* Using job '{self.job}' from {conf_fn}")
        self.conf = config[self.job]

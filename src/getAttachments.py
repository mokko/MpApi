"""
getAttachments downloads attachments from RIA

create a configuration file that describes one or multiple jobs
e.g. getAttachments.jobs
label:
    type: group
    id: 12345
    restriction: None | freigegeben
    name: dateiname | mulid
(where | indicates the possible options).

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
from mpapi.module import Module
from mpapi.search import Search
from pathlib import Path

conf_fn = "getAttachments.jobs"
response_cache = "_ga_response.xml"  # for debugging
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}


class GetAttachments:
    def __init__(self, *, baseURL: str, job: str, user: str, pw: str) -> None:
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.job = job
        self.setup_conf()

        # if Path(response_cache).exists():
        #    print(f"* loading response cache from '{response_cache}'")
        #    m = Module(file=response_cache)
        # else:
        print(f"* launching new query")
        m = self.query()
        m.toFile(path=response_cache)  # debug
        self.process_response(data=m)

    def process_response(self, *, data: Module):  # returns nothing useful
        no = data.actualSize(module="Multimedia")
        name_policy = self.conf["name"]
        print(f"* {no} digital assets found")

        yyyymmdd = date.today().strftime("%Y%m%d")
        out_dir = Path(self.job).joinpath(yyyymmdd)

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
            print(f"*  mulId {ID}")  # {dateiname}
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
        """
        Restriction: Currently, only gets attachments from Multimedia.
        """
        print(f"* type: {self.conf['type']}")
        print(f"* id: {self.conf['id']}")  # id is group id
        qu = Search(module="Multimedia")
        if self.conf["restriction"] == "freigegeben":
            qu.AND()
        elif self.conf["type"] == "approval":
            raise SyntaxError("ERROR: approval group mode not implemented yet!")
        if self.conf["type"] == "group":
            qu.addCriterion(  #  get assets attached to objects in a given group
                operator="equalsField",
                field="MulObjectRef.ObjObjectGroupsRef.__id",
                value=self.conf["id"],
            )
        elif self.conf["type"] == "exhibit":
            print("WARN: exhibit mode not tested yet!")
            qu.addCriterion(  #  get assets attached to objects in a given exhibition
                operator="equalsField",
                field="MulObjectRef.ObjRegistrarRef.RegExhibitionRef.__id",
                value=self.conf["id"],
            )
        elif self.conf["type"] == "loc":
            print("WARN: location mode not tested yet!")
            qu.addCriterion(  #  get assets attached to objects at a given location
                operator="equalsField",
                field="MulObjectRef.ObjCurrentLocationVoc",
                value=self.conf["id"],
            )

        elif self.conf["type"] == "restExhibit":
            # get assets attached to restauration records attached to an exhibit
            # photos are typically not SMB-approved
            qu.addCriterion(
                operator="equalsField",
                field="MulConservationRef.ConExhibitionRef.__id",
                value=self.conf["id"],
            )
        else:
            raise TypeError(f"ERROR: This type is not known! {self.conf['type']}")
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

    def setup_conf(self):
        """
        Saves configuration for selected job in self.conf
        """
        config = configparser.ConfigParser()
        if not Path(conf_fn).exists():
            raise SyntaxError(f"ERROR: conf file not found! {conf_fn}")
        config.read(conf_fn)
        print(f"* Using job '{self.job}' from {conf_fn}")
        self.conf = config[self.job]

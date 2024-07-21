"""
getAttachments downloads attachments from RIA

Configuration file format (where | indicates the possible options):
#file is typically named 'getAttachments.jobs'
[label]
    type = "group" | "exhibit" | "loc" | "query" | "restExhibit"
    id: 12345
    label: "alabel"
    restriction: "keine" | "freigegeben"
    name: "dateiname" | "mulid" | "Cornelia"

    keine : download the attachments from all assets
    freigegeben : download only assets which are freigegeben for SMB-Digital
    Cornelia: mulId.jpg in folder Standardbild or nichtStandardbild
    mulid: muldId.jpg
    dateiname: dateiname.jpg

USAGE
    getAttachments -j label
    getAttachments -j m39 -c path/to/m39.xml

will put attachments in dir
    ./label/20220708/pix
where the current date is used for the second directory.

NEW
- 21.7.2024: We're using the downloaded data from MpApi as the cache, ao we dont
    have to d/n same stuff again.
"""

from datetime import date
from lxml import etree
from mpapi.client import MpApi
from mpapi.constants import get_credentials, load_conf
from mpapi.module import Module
from mpapi.search import Search
from pathlib import Path

conf_fn = "jobs.toml"
NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}


def get_attachment(client: MpApi, ID: int) -> None:
    """
    Get attachment from a single Multimedia ID and save it to disk. There can be only
    one or none attachment.

    This function profits from its more recent inception. Uses underscore in name,
    function instead of method, no keyword argument.
    """

    print(f"Getting Multimedia {ID}")
    # we need the dateiname to save, assuming there can be only one.
    m = client.getItem2(mtype="Multimedia", ID=ID)
    # m.toFile(path=f"debug.multimedia{ID}")
    if (
        m.xpath("/m:application/m:modules/m:module/m:moduleItem/@hasAttachments")[0]
        != "true"
    ):
        raise ValueError("ERROR: Record has no attachment")

    try:
        fn = m.xpath(
            "/m:application/m:modules/m:module/m:moduleItem/m:dataField[@name='MulOriginalFileTxt']/m:value/text()"
        )[0]
    except Exception:
        fn = f"{ID}.jpg"  # use mulId as a fallback if no dateiname in RIA
        print("WARNING: Falling back to {fn} since no Dateiname specified in RIA")

    print(f"About to save attachment to '{fn}'")
    client.saveAttachment(id=ID, path=fn)


class GetAttachments:
    def __init__(
        self, *, job: str, cache: str | None = None, force: bool = False
    ) -> None:
        user, pw, baseURL = get_credentials()
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)
        self.conf = self.setup_conf(job)
        self.job = job
        self.force = force
        # default for saving new request
        # if we're not using a cache
        cache_fn = f"mul_{self.conf['type']}{self.conf['id']}.xml"

        if cache:
            self.cache = Path(cache)
            print("* loading cached response")
            m = Module(file=cache)
        else:
            print("* launching new search")
            self.cache = cache_fn
            m = self.query()
            m.toFile(path=cache_fn)

        if self.conf["attachments"]["name"] == "Cornelia":
            # if self.conf["type"] != "group":
            #    raise SyntaxError("Cornelia mode only works with groups")
            # in this mode we need object data...
            # print("Cornelia mode (Standardbild in separate folder)")
            self.objData = self._init_ObjData()

        self.process_response(data=m)

    def process_response(self, *, data: Module) -> None:
        print("* processing response")
        no = data.actualSize(module="Multimedia")
        print(f"* {no} assets found")
        out_dir = self._get_out_dir()

        match self.conf["attachments"]["restriction"]:
            case "keine":
                moduleItemsL = data.xpath(f"""
                /m:application/m:modules/m:module[
                    @name = 'Multimedia'
                ]/m:moduleItem""")
            case "freigegeben":
                moduleItemsL = data.xpath(f"""
                /m:application/m:modules/m:module[
                    @name = 'Multimedia'
                ]/m:moduleItem[
                    m:repeatableGroup[
                        @name = 'MulApprovalGrp'
                    ]/m:repeatableGroupItem[
                        m:vocabularyReference[
                            @name='TypeVoc'
                        ]/m:vocabularyReferenceItem[
                            @name = 'SMB-digital' 
                        ] 
                    and m:vocabularyReference[
                        @name='ApprovalVoc'
                        ]/m:vocabularyReferenceItem[
                            @name = 'Ja' 
                        ]
                    ]
                ]""")
                # for each in freigegebenL:
                #   print (etree.tostring(each, pretty_print=True, encoding="unicode"))
                # raise SyntaxError("Stop here")
        print(f"*  About to loop thru {len(moduleItemsL)} assets.")

        for itemN in moduleItemsL:
            ID = itemN.get("id")
            if itemN.get("hasAttachments") == "true":
                self._get_single_attachment(item=itemN, ID=ID, out_dir=out_dir)
            else:
                print(f"*  mulId {ID} no attachment")

    def query(self) -> Module:
        """
        Restriction: Currently, only gets attachments from Multimedia.
        """
        qu = Search(module="Multimedia")
        if self.conf["attachments"]["restriction"] == "freigegeben":
            qu.AND()

        qu = self._qm_type(query=qu, Id=self.conf["id"])

        match self.conf["attachments"]["restriction"]:
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
            case "alle":
                pass
            case _:
                raise SyntaxError(
                    f"Unknown restriction value {self.conf['attachments']['restriction']}"
                )
        qu.addField(field="MulOriginalFileTxt")  # speeds up query a lot!
        qu.validate(mode="search")
        print(f"* about to execute query\n{qu.toString()}")
        return self.api.search2(query=qu)

    def setup_conf(self, job: str) -> dict:
        """
        Returns configuration for selected job
        """
        if not Path(conf_fn).exists():
            raise SyntaxError(f"ERROR: conf file not found! {conf_fn}")
        config_data = load_conf(conf_fn)

        try:
            job_data = config_data[job]
        except KeyError:
            raise SyntaxError(f"Job '{job}' not known in configuration")

        required = ["type", "id", "attachments"]
        # print(f"* Using job '{self.job}' from {conf_fn}")

        for each in required:
            try:
                job_data[each]
            except Exception:
                raise SyntaxError(f"Config value {each} missing!")

        # print(f"   {job_data=}")
        return job_data

    #
    # somewhat private
    #

    def _get_dateiname(self, item) -> str:
        try:
            dateiname = item.xpath(
                "./m:dataField[@name='MulOriginalFileTxt']/m:value/text()",
                namespaces=NSMAP,
            )[0]
        except Exception:
            ID = item.xpath("@id")[0]
            dateiname = f"{ID}.jpg"  # use mulId as a fallback if no dateiname in RIA
            # there is a chance that this file is no jpg
            print(
                f"WARNING: Falling back to ID {dateiname} since no Dateiname specified in RIA"
            )
        return dateiname

    def _get_obj_group(self, *, grpId: int) -> Module:
        qu = Search(module="Object")
        qu.addCriterion(
            operator="equalsField",
            field="ObjObjectGroupsRef.__id",
            value=str(grpId),
        )
        # would speed up query a lot, but we cant get it to work!
        # qu.addField(field="ObjMultimediaRef")
        # qu.addField(field="ObjMultimediaRef.moduleReferenceItem")
        # qu.addField(field="ObjMultimediaRef.moduleReferenceItem.dataField.ThumbnailBoo")
        qu.validate(mode="search")
        print(f"* about to execute query\n{qu.toString()}")
        return self.api.search2(query=qu)

    def _get_single_attachment(self, *, item, ID: int, out_dir: Path) -> None:
        dateiname = self._get_dateiname(item)  # may fail if no attachment
        suffix = Path(dateiname).suffix

        print(f"*  mulId {ID}")  # {dateiname}

        match self.conf["attachments"]["name"]:
            case "Cornelia":
                res = self.objData.xpath(f"""
                /m:application/m:modules/m:module[
                    @name = 'Object'
                ]/m:moduleItem/m:moduleReference[
                    @name = 'ObjMultimediaRef'
                ]/m:moduleReferenceItem[
                    @moduleItemId =  {ID}
                ]/m:dataField[
                    @name = 'ThumbnailBoo'
                ][m:value = 'true']""")
                # print(f"xxxxxxxxxxxxxxxx {res=}")
                if len(res) > 0:
                    out_dir2 = out_dir / "Standardbild"
                else:
                    out_dir2 = out_dir / "nichtStandardbild"
                out_dir2.mkdir(exist_ok=True)
                path = out_dir2 / f"{ID}{suffix}"
            case "mulId":
                suffix = Path(dateiname).suffix
                path = out_dir / f"{ID}{suffix}"
            case "dateiname":
                path = out_dir / dateiname  # includes suffix
            case _:
                raise SyntaxError(f"Error: Unknown config value: {self.conf['name']}")

        if not path.exists() or self.force:  # let's not overwrite existing files
            print(f"\t{path} {self.force=}")
            try:
                self.api.saveAttachment(id=ID, path=path)
            except KeyboardInterrupt:
                print("Catch keyboard interupt")
        else:
            print("\tfile exists already on disk and force off")

    def _get_out_dir(self) -> Path:
        """
        Determines directory for saving pix in; makes it if it doesn't exist
        yet.
        """
        yyyymmdd = date.today().strftime("%Y%m%d")
        out_dir = Path(self.job) / yyyymmdd / "pix"

        if not out_dir.exists():
            print(f"* Making dir {out_dir}")
            out_dir.mkdir(parents=True)
        return out_dir

    def _init_ObjData(self) -> None:
        obj_fn = Path(f"obj_{self.conf['type']}{self.conf['id']}.xml")
        if self.cache.exists():
            ObjData = Module(file=str(self.cache))
        elif obj_fn.exists():
            ObjData = Module(file=obj_fn)
        else:
            ObjData = self._get_obj_group(grpId=self.conf["id"])
            ObjData.toFile(path=obj_fn)
        return ObjData

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
                    value=str(Id),
                )
            case "loc":
                print("WARN: location mode not tested yet!")
                query.addCriterion(  #  get assets attached to objects at a given location
                    operator="equalsField",
                    field="MulObjectRef.ObjCurrentLocationVoc",
                    value=Id,
                )
            case "query":
                # saved query
                # I cant get the list of assets associated with a saved query through
                # extended search
                # why don't we use the already downloaded cache file?
                raise TypeError("Not yet implemented!")
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

        return query

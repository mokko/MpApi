"""
quick and dirty commandline utitly for ccc portal. It reads in a series of zipped chunks,
unpacks them, filters out Multimedia items that are freigegeben, but still not available
on recherche.smb.museum.

pdf werden nicht auf recherche angezeigt, selbst wenn diese Assets eine Freigabe haben.
tif werden als jpg angezeigt, wenn sie entsprechende Freigabe haben.
"""

import logging

# from lxml import etree  # type: ignore
from mpapi.constants import NSMAP
from mpapi.module import Module
from pathlib import Path
import re
import sys
from typing import Iterable
from zipfile import ZipFile


def iter_chunks(src: Path) -> Iterable[Path]:
    """
    returns generator with path for existing files, counting up as long
    files exist. For this to work, filename has to include
        path/to/group1234-chunk1.xml

    This might belong in chunker.py to be reusable. Chunker requires ps, user
    and baseURL.
    """
    print(f"chunk src: {src}")
    parent, beginning, no, tail = _analyze_chunkFn(src=src)
    chunkFn = Path(src)

    while chunkFn.exists():
        yield chunkFn
        # print(f"{chunkFn} exists")
        no += 1
        chunkFn = Path(parent / f"{beginning}-chunk{no}{tail}")


def filter_(src: str, force: bool = False) -> None:
    """
    Expect chunks like this

    C:/m3/MpApi/sdata/CCC/cccall/20240610/query767070-chunk1.zip
    """
    src = Path(src)
    target_dir = src.parent.parent / f"{src.parent.name}" / "filter"
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
    print(f"{target_dir=}")
    _init_log(target_dir)
    src_dir = src.parent
    for src_zip in iter_chunks(src):
        member = Path(src_zip).with_suffix(".xml").name
        temp_fn = src_dir / member
        target_fn = target_dir / member
        target_zip = target_fn.with_suffix(".zip")
        # print(f"{target_dir=}")
        # print(f"{target_fn=}")
        # print(f"{target_zip=}")
        # print(f"{member=}")
        # print(f"{src_zip=}")
        # if src_zip.exists():
        # print("src_zip exists")
        # else:
        # print("src_zip DOES NOT exists")

        if not target_zip.exists() or force:
            if not temp_fn.exists():
                with ZipFile(src_zip, "r") as zippy:
                    print("unzipping...")
                    zippy.extractall(src_dir)
            m = _unpublished(data=Module(file=temp_fn))
            m = _only_em(data=m)
            m.toZip(path=target_fn)
        if temp_fn.with_suffix(".zip").exists() and temp_fn.exists():
            print("unlinking temp file")
            temp_fn.unlink()


#
# more private
#


def _analyze_chunkFn(src: Path) -> tuple[Path, str, int, str]:
    """
    split path into four components.
    """
    parent = src.parent
    # print(f"ENTER ANALYZE WITH {src}")
    partsL = str(src).split("-chunk")
    root = partsL[0]
    m = re.match(r"(\d+)[\.-]", partsL[1])
    if m is not None:
        no = int(m.group(1))
    tail = str(src).split("-chunk" + str(no))[1]
    # print(f"_ANALYZE '{root}' '{no}' '{tail}'")
    return parent, root, no, tail


def _init_log(target_dir: Path) -> None:
    logging.basicConfig(
        datefmt="%Y%m%d %I:%M:%S %p",
        filename=Path(target_dir) / "filter.log",
        filemode="a",  # append now since we're starting a new folder
        # every day now anyways.
        level=logging.DEBUG,
        format="%(asctime)s: %(message)s",
    )
    log = logging.getLogger()
    log.addHandler(logging.StreamHandler(sys.stdout))


def _only_em(*, data: Module) -> Module:
    """
    drop moduleItems that are have verwaltendeInstituion = Ethnologisches Museum
    """
    xpath = """/m:application/m:modules/m:module[
        @name = 'Object'
    ]/m:moduleItem[
        m:moduleReference[
            @name ='ObjOwnerRef'
        ]/m:moduleReferenceItem/m:formattedValue[
            @language='de'
        ] != 'Ethnologisches Museum, Staatliche Museen zu Berlin'
    ]"""
    for itemN in data.xpath(xpath):
        inst = itemN.xpath(
            "m:moduleReference[@name ='ObjOwnerRef']/m:moduleReferenceItem/m:formattedValue/text()",
            namespaces=NSMAP,
        )[0]
        print(f"Unlinking object with verwaltendeInstituion != EM {inst}")
        itemN.getparent().remove(itemN)
    return data


def _unpublished(*, data: Module) -> Module:
    """
    src_xml is the path to the unpacked xml file
    target_dir is the path to the target directory

    The respective Multimedia moduleItems get deleted, the entry in moduleReferenceItem
    remain...
    """
    for itemN in data.xpath("""/m:application/m:modules/m:module[
        @name = 'Multimedia'
        ]/m:moduleItem"""):
        # print(f"{itemN=}")zu
        dateinameL = itemN.xpath(
            """m:dataField[
            @name = 'MulOriginalFileTxt'
        ]/m:value/text()""",
            namespaces=NSMAP,
        )
        if len(dateinameL) > 0 and dateinameL[0].endswith(
            (".mp3", ".pdf", "mp4", ".wav")
        ):
            mulId = itemN.xpath("@id")[0]
            logging.info(f"DEL {mulId} {dateinameL[0]}")
            itemN.getparent().remove(itemN)
    return data

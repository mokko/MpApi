"""
commandline utitly that reads in a series of zipped chunks, unpacks them, filters out
Multimedia items that are freigegeben, but still not available on recherche.smb.museum.

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
    chunkFn = src

    while Path(chunkFn).exists():
        yield chunkFn
        # print(f"{chunkFn} exists")
        no += 1
        chunkFn = parent / f"{beginning}-chunk{no}{tail}"


def filter_unpublished(src: str, force: bool = False) -> None:
    """
    Expect chunks like this

    C:/m3/MpApi/sdata/CCC/cccall/20240610/query767070-chunk1.zip
    """
    src = Path(src)
    pro_dir = src.parent.parent
    target = pro_dir / f"{src.parent.name}" / "filter"
    if not target.exists():
        target.mkdir(parents=True)
    # print(f"target:{target}")
    _init_log(target)
    pdir = src.parent
    for p in iter_chunks(src):
        member = Path(p).with_suffix(".xml")
        temp_fn = pdir / member

        if not temp_fn.exists():
            with ZipFile(p, "r") as zippy:
                print("unzipping...")
                zippy.extractall(pdir)
        _per_chunk(src_xml=temp_fn, target_dir=target, force=force)
        if temp_fn.with_suffix(".zip").exists():
            print("unlinking")  # {temp_fn}
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


def _per_chunk(*, src_xml: Path, target_dir: Path, force: bool) -> None:
    """
    src_xml is the path to the unpacked xml file
    target_dir is the path to the target directory

    The respective Multimedia moduleItems get deleted, the entry in moduleReferenceItem
    remain...
    """
    new_fn = target_dir / src_xml.name
    zip_fn = new_fn.with_suffix(".zip")
    if not zip_fn.exists() or force:
        m = Module(file=src_xml)
        for itemN in m.xpath("""/m:application/m:modules/m:module[
            @name = 'Multimedia'
            ]/m:moduleItem"""):
            # print(f"{itemN=}")zu
            dateiname = itemN.xpath(
                """m:dataField[
                @name = 'MulOriginalFileTxt'
            ]/m:value/text()""",
                namespaces=NSMAP,
            )
            if len(dateiname) > 0 and dateiname[0].endswith(
                (".mp3", ".pdf", "mp4", ".wav")
            ):
                mulId = itemN.xpath("@id")[0]
                logging.info(f"{src_xml.name}: DEL {mulId} {dateiname[0]}")
                itemN.getparent().remove(itemN)
        print(f"writing to {zip_fn}")
        m.toZip(path=new_fn)  # overwriting existing file
    else:
        print(f"target zip exists already: {zip_fn}")

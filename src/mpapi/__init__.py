"""Unofficial Open Source Client for the MuseumPlus API written in Python"""

__version__ = "0.1.10"  # unified toml configuration
import argparse
from mpapi.filterUnpublished import filter_
from mpapi.getAttachments import GetAttachments, get_attachment
from mpapi.client import MpApi
from mpapi.constants import get_credentials
from mpapi.mink import Mink, arg as mink_arg
from mpapi.module import Module
from mpapi.validate import Validate
from pathlib import Path
import sys

user, pw, baseURL = get_credentials()

allowed_mtypes = (
    "Accessory",
    "Address",
    "AddressGroup",
    "CollectionActivity",
    "Conservation",
    "Contract",
    "Datasource",
    "DefDimension",
    "DefLiterature",
    "Event",
    "Exhibition",
    "Function",
    "FunctionGenerator",
    "Import",
    "ImportDefinition",
    "InventoryNumber",
    "Literature",
    "Movement",
    "Multimedia",
    "MultimediaGroup",
    "Object",
    "ObjectGroup",
    "OrganisationUnit",
    "Ownership",
    "Parameter",
    "Person",
    "Place",
    "Registrar",
    "Search",
    "Task",
    "Template",
    "User",
    "UserGroup",
)


def _login() -> MpApi:
    print(f"Logging in as '{user}'")
    return MpApi(baseURL=baseURL, pw=pw, user=user)


def _require(args, required_args: list) -> None:
    """
    Since with nargs argparse can't use the required argument, we roll our own.
    """
    for req in required_args:
        if req not in args:
            raise SyntaxError("Required args not provided")


def _setup_args(parser):
    parser.add_argument(
        "-v", "--version", help="Display version information", action="store_true"
    )
    args = parser.parse_args()
    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)
    return args


def filter():
    # filter out multimedia items that are not really published on researche.smb.museum
    parser = argparse.ArgumentParser(
        description="discard multimedia assets that are not public although freigegeben(mp3,wav,pdf,mp4)."
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite existing zip files",
    )
    parser.add_argument(
        "-s",
        "--src",
        help="input file",
    )
    args = _setup_args(parser)
    filter_(src=args.src, force=args.force)


def getAttachment():
    parser = argparse.ArgumentParser(
        description="simple getAttachment for attachments of single asset record"
    )
    parser.add_argument(
        "ID",
        nargs="?",
        help="ID as integer for the Multimedia record you want the attachment from",
    )
    args = _setup_args(parser)
    _require(args, ["ID"])
    c = _login()
    get_attachment(c, args.ID)


def getAttachments():
    """
    for config file format see getAttachments.py
    """
    parser = argparse.ArgumentParser(
        description="getAttachments for MpApi (using config file)"
    )
    parser.add_argument(
        "-c",
        "--cache",
        help="Specify cache file",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--force",
        help="overwrite existing attachments with me download",
        action="store_true",
    )
    parser.add_argument(
        "-j", "--job", required=True, help="pick a job from getAttachments.jobs file"
    )
    args = _setup_args(parser)
    GetAttachments(job=args.job, cache=args.cache, force=args.force)


def getDefinition():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument(
        "-t",
        "--mtype",
        help="module type (Object, Multimedia etc.); optional",
        default=None,
    )
    args = _setup_args(parser)
    c = _login()

    m = c.getDefinition2(mtype=args.mtype)
    if args.mtype is None:
        fn = "definition.xml"
    else:
        fn = f"definition-{args.mtype}.xml"
    print(f"About to write to {fn}")
    if Path(fn).exists():
        print("   overwriting existing file")
    m.toFile(path=fn)


def getItem():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument(
        "-t", "--mtype", help="module type (Object, Multimedia etc.)", default="Object"
    )
    parser.add_argument(
        "-u", "--upload", help="Save in upload form", action="store_true"
    )
    parser.add_argument("-i", "--ID", help="ID")
    args = _setup_args(parser)

    if args.mtype not in allowed_mtypes:
        print(f"WARNING: Unknown type. Known types: {allowed_mtypes}")

    c = _login()
    m = c.getItem2(mtype=args.mtype, ID=args.ID)
    if args.upload:
        fn = f"getItem-{args.mtype}{args.ID}u.xml"
    else:
        fn = f"getItem-{args.mtype}{args.ID}.xml"

    print(f"About to write to {fn}")
    if Path(fn).exists():
        print("   overwriting existing file")
    if args.upload:
        m.clean()  # rm uuids
        m.uploadForm()
    m.toFile(path=fn)


def mink():
    mink_arg()


def updateItem():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument("-f", "--file", help="File location to upload")
    parser.add_argument("-i", "--id", help="moduleItem/@id")
    parser.add_argument("-t", "--mtype", help="module type")
    args = _setup_args(parser)

    # todowe could extract module type and id from the record
    _require(args, ["file", "id", "mtype"])

    m = Module(file=args.file)
    c = _login()
    m = c.uploadItem2(mtype=args.mtype, ID=args.ID)
    print(m)


def validate():
    parser = argparse.ArgumentParser(description="validate for MpApi")
    parser.add_argument(
        "-m", "--mode", help="mode (module, search or vocabulary)", default="module"
    )
    parser.add_argument("file", nargs="?")
    args = _setup_args(parser)
    if args.file is None:
        raise SyntaxError("ERROR: Required arg 'file' not provided!")

    v = Validate(path=args.file)
    v.validate(mode=args.mode)

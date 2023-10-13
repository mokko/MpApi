"""An Unofficial Open Source Client for the MuseumPlus API"""

__version__ = "0.1.9"  # replace pyexiv, cleanup __init__
import argparse
from getAttachments import GetAttachments
from mpapi.mink import Mink
from mpapi.module import Module
from mpapi.client import MpApi
from mpapi.constants import get_credentials
from mpapi.validate import Validate
from pathlib import Path
import sys


def _login() -> MpApi:
    user, pw, baseURL = get_credentials()
    c = MpApi(baseURL=baseURL, pw=pw, user=user)


def _setup_args(parser):
    parser.add_argument(
        "-v", "--version", help="Display version information", action="store_true"
    )
    args = parser.parse_args()
    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)
    return args


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

    print(f"Logging in as '{user}'")
    m = c.getDefinition2(mtype=args.mtype)
    if args.mtype is None:
        fn = f"definition.xml"
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


def getAttachments():
    parser = argparse.ArgumentParser(description="getAttachments for MpApi")
    parser.add_argument(
        "-j", "--job", required=True, help="pick a job from getAttachments.jobs file"
    )
    args = _setup_args(parser)

    GetAttachments(baseURL=baseURL, job=args.job, user=user, pw=pw)


def mink():
    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")  # , required=True
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = _setup_args(parser)

    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)


def updateItem():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument("-f", "--file", help="File location to upload")
    parser.add_argument("-i", "--id", help="moduleItem/@id")
    parser.add_argument("-t", "--mtype", help="module type")
    args = _setup_args(parser)

    # todowe could extract module type and id from the record

    required_args = ["file", "id", "mtype"]

    for req in required_args:
        if not req in args:
            raise SyntaxError("Required args not provided")

    m = Module(file=args.file)
    c = _login()
    m = c.uploadItem2(mtype=args.mtype, ID=args.ID)


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

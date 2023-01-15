"""An Unofficial Client for the MuseumPlus API"""

__version__ = "0.1.5"
credentials = "credentials.py"  # expect credentials in pwd
import argparse
from getAttachments import GetAttachments
from mink import Mink
from mpapi.module import Module
from mpapi.client import MpApi
from pathlib import Path
from replace import Replace

if Path(credentials).exists():
    with open(credentials) as f:
        exec(f.read())


def mink():
    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run")  # , required=True
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    parser.add_argument("-v", "--version", help="Display version information")
    args = parser.parse_args()
    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)
    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)


def updateItem():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument("-f", "--file", help="File location to upload")
    parser.add_argument("-i", "--id", help="moduleItem/@id")
    parser.add_argument("-t", "--mtype", help="module type")
    parser.add_argument("-v", "--version", help="Display version information")

    # todowe could extract module type and id from the record

    required_args = ["file", "id", "mtype"]

    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)

    for req in required_args:
        if not req in args:
            raise SyntaxError("Required args not provided")

    args = parser.parse_args()
    m = Module(file=args.file)
    c = MpApi(baseURL=baseURL, pw=pw, user=user)
    m = c.uploadItem2(mtype=args.mtype, ID=args.ID)


def getItem():
    parser = argparse.ArgumentParser(description="getItem for MpApi")
    parser.add_argument(
        "-t", "--mtype", help="module type (Object, Multimedia etc.)", default="Object"
    )
    parser.add_argument(
        "-u", "--upload", help="Save in upload form", action="store_true"
    )
    parser.add_argument("-i", "--ID", help="ID")
    parser.add_argument("-v", "--version", help="Display version information")
    args = parser.parse_args()

    if args.version:
        print(f"Version: {__version__}")
        sys.exit(0)

    c = MpApi(baseURL=baseURL, pw=pw, user=user)
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
    args = parser.parse_args()
    GetAttachments(baseURL=baseURL, job=args.job, user=user, pw=pw)


def replace():
    # credentials = "emem1.py"  # in pwd
    parser = argparse.ArgumentParser(description="Command line frontend for Replace.py")
    parser.add_argument(
        "-l",
        "--lazy",
        help="lazy modes reads search results from a file cache, for debugging",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--act",
        help="include action, without it only show what would be changed",
        action="store_true",
    )
    parser.add_argument(
        "-j", "--job", help="load a plugin and use that code", required=True
    )
    parser.add_argument(
        "-L", "--Limit", help="set limit for initial search", default="-1"
    )
    args = parser.parse_args()
    replacer = Replace(baseURL=baseURL, pw=pw, user=user, lazy=args.lazy, act=args.act)
    plugin = replacer.job(plugin=args.job)
    replacer.runPlugin(plugin=plugin, limit=args.Limit)  # set to -1 for production

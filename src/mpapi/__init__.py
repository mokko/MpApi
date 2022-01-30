"""An Unofficial Client for the MuseumPlus API"""

__version__ = "0.1.3"
credentials = "credentials.py"  # expect credentials in pwd
import argparse

from replace import Replace
from mink import Mink
from pathlib import Path

if Path(credentials).exists():
    with open(credentials) as f:
        exec(f.read())


def mink():
    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run", required=True)
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()
    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)


def replace():
    credentials = "emem1.py"  # in pwd
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

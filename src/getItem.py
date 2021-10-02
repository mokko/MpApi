"""
I want Multimedia 271188 on disk
"""
import os
import sys
# what the heck?
if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])
credentials = "credentials.py"  # expect credentials in pwd

from Module import Module
from MpApi import MpApi
from pathlib import Path
import requests
from Search import Search
from lxml import etree  # necessary?

if __name__ == "__main__":
    import argparse

    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Command line tool to save a single item on disk")
    parser.add_argument("-m","--module", help="module (e.g. Object or Multimedia", required=True)
    parser.add_argument("-i","--id", help="id", required=True)

    args = parser.parse_args()

    client = MpApi(baseURL=baseURL, user=user, pw=pw)
    r = client.getItem(module=args.module,id=args.id)
    out_fn = f"{args.module}{args.id}.xml"
    print (f"Writing to {out_fn}")
    client.toFile(xml=r.text, path=out_fn)
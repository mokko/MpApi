from lxml import etree
from pathlib import Path

try:
    import tomllib  # new in Python v3.11
except ModuleNotFoundError:
    import tomli as tomllib  # < Python v3.11


NSMAP = {
    "m": "http://www.zetcom.com/ria/ws/module",
    "o": "http://www.zetcom.com/ria/ws/module/orgunit",
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "v": "http://www.zetcom.com/ria/ws/vocabulary",
}


parser = etree.XMLParser(remove_blank_text=True)


# not exactly a constant, but dont know where else to put this function
def get_credentials() -> tuple[str, str, str]:
    cred_fn = Path.home() / ".ria"
    if not cred_fn.exists():
        raise SyntaxError(f"RIA Credentials not found at {cred_fn}")

    with open(cred_fn, "rb") as f:
        cred = tomllib.load(f)

    user = cred["user"]
    pw = cred["pw"]
    baseURL = cred["baseURL"]

    return user, pw, baseURL

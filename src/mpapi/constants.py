from lxml import etree

credentials = "credentials.py"

NSMAP = {
    "m": "http://www.zetcom.com/ria/ws/module",
    "o": "http://www.zetcom.com/ria/ws/module/orgunit",
    "s": "http://www.zetcom.com/ria/ws/module/search",
}


parser = etree.XMLParser(remove_blank_text=True)

"""

Load vocabulary documents in analogy to mpapi.module

"""
from lxml import etree
from mpapi.helper import Helper
from mpapi.constants import parser, NSMAP
from typing import Any, Optional


class Vocabulary(Helper):
    def __init__(self, *, xml: Optional[str] = None, file: Optional[str] = None):
        if file is not None:
            self.etree = etree.parse(str(file), parser)
        if xml is not None:
            xml = xml.encode()
            self.etree = etree.fromstring(xml, parser)

    def __iter__(self) -> Any:
        """
        iterates through all nodes
            v = Vocabulary(xml=xml)
            for node in v:
                #do something with node
        """
        nodesL = self.xpath("//v:node")
        yield from [nodeN for nodeN in nodesL]

    def __len__(self):
        """
        Returns the number of all nodes, similar to size. Also gets
        used when thruthyness of a module object gets evaluated (where 0 items
        is considered False).
            v = vocabulary()
            if not v:
                # get here

        to check for v's existence:
            try:
                v
        to check type:
            isinstance(v, Vocabulary)
        """
        return int(self.xpath("count(//v:node|/v:instance)"))

from mpapi.helper import Helper
from mpapi.constants import parser
from lxml import etree


class Validate(Helper):
    def __init__(self, *, path: str) -> None:
        self.etree = etree.parse(str(path), parser)

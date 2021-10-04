# -*- coding: UTF-8
from lxml import etree

parser = etree.XMLParser(remove_blank_text=True)  # why is the default encoding=None
E = etree.fromstring("<root>äöü</root>", parser)

tree = etree.ElementTree(E)
tree.write("writtenWithL3.xml", pretty_print=True, encoding="UTF-8")

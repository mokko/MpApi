"""
<repeatableGroup name="ObjTextGrp" size="1">
    <repeatableGroupItem id="44219535">
        <dataField dataType="Clob" name="TextHTMLClb">
            <value>ananda lahari (&#252;bers. "Woge der Wonne")- doppelte Zupftrommel. 
                "Eine Darmsaite verbindet die Felle zweier verschiedengro&#223;er h&#246;lzener 
                Trommeln" (Curt, Sachs: "Die Musikinstrumente Indiens und Indonesiens", 1923, S.79)
            </value>
        </dataField>
        ...

For now we're not expecting to load individual repeatableGroups from disk, so making 
them from scratch only.

"""
from lxml import etree
from Helper import Helper

NSMAP = {"m": "http://www.zetcom.com/ria/ws/module"}

class repeatableGroup (Helper):
    def __init__(self, *, name, size):
        self.etree = etree.Element("{http://www.zetcom.com/ria/ws/module}repeatableGroup", 
            name=name, size=size)
    def item(self, *, id=None, item=None):
        if id is None and item is None:
            raise TypeError("item needs id or an item object!")
        elif item is not None:
            moduleN = self.etree.xpath("/m:application/m:modules/m:module[last()]", namespaces=NSMAP)[0]
            moduleN.append(item.etree)
        elif id is not None:
            #getter, should return one repeatableGroup
            return self.etree.xpath("/m:application/m:modules/m:module[]", namespaces=NSMAP)[id]


class repeatableGroupItem (Helper):
    def __init__(self, *, id):
        self.etree = etree.Element("{http://www.zetcom.com/ria/ws/module}repeatableGroupItem", 
            name=name, size=size)
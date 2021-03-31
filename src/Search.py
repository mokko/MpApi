"""
Make the Search request in xml from scratch

Specification: http://docs.zetcom.com/ws/module/search/search.xml

Currently, we're making only expert searches.

We're using a different lingo here than Zetcom. For us an expert search can
contain different criteria. Criteria have three components
- a field (e.g. __id)
- an operator (e.g. isNull)
- and a value (e.g.

With some operators, such as isNull, no value is needed/allowed.

Each criterion can be combined with others using the usual conjunctions (and, 
or, not). 

USAGE
    s = mpSearch(module="Object", limit=-1, offset=0)
    s.AND
    s.addCriterion (operator="equalsValue", field="__id", value="1234")
    s.addCriterion (operator="equalsValue", field="__id", value="1234")

#helpers
    print(s.toString())
    s.toFile(path="out.xml")
    s.validate()
    
self.etree stores the lxml object containing the xml document.

EXAMPLE
<application 
    xmlns="http://www.zetcom.com/ria/ws/module/search" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd">
    <modules>
        <module name="ObjectGroup">
            <search limit="10" offset="0">
                <expert>
                    <and>
                      <equalsField fieldPath="__id" operand="29825" />
                    </and>
                </expert>
            </search>
        </module>
    </modules>
</application>

"""

from pathlib import Path
from lxml import etree
from Helper import Helper

# xpath 1.0 and lxml don't empty string or None for default ns
NSMAP = {"s": "http://www.zetcom.com/ria/ws/module/search"}

allowedOperators = {
    "betweenIncl",
    "betweenExcl",
    "contains",
    "endsWithField",
    "endsWithTerm",
    "equalsField",
    "equalsTerm",
    "greater",
    "greaterEquals",
    "isNotNull",
    "isNull",
    "isNotBlank",
    "isBlank",
    "less",
    "lessEquals",
    "notEqualsField",
    "notEqualsTerm",
    "startsWithField",
    "startsWithTerm",
}  # let's use an inmutable set


class Search (Helper):
    def __init__(self, *, module, limit=-1, offset=0):

        # vanilla version without a single and
        xml = f"""<application 
        xmlns="http://www.zetcom.com/ria/ws/module/search" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search 
        http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd">
        <modules>
            <module name="{module}">
                <search limit="{limit}" offset="{offset}">
                    <expert>
                    </expert>
                </search>
            </module>
        </modules>
        </application>"""
        parser = etree.XMLParser(remove_blank_text=True)
        self.etree = etree.fromstring(xml, parser)

    def addCriterion(self, *, operator, field, value=None):
        if operator not in allowedOperators:
            raise TypeError(f"Unknown operator: '{operator}'")

        parentN = self._findParent()
        # expertN = self.etree.xpath(
        #    "/s:application/s:modules/s:module/s:search/s:expert",
        #    namespaces=NSMAP)
        etree.SubElement(
            parentN,
            "{http://www.zetcom.com/ria/ws/module/search}" + operator,
            fieldPath=field,
            operand=value,
        )

    #
    # conjunctions
    #

    def AND(self, *, modifier=False):
        self._addConjunction("and", modifier)

    def OR(self, *, modifier=False):
        self._addConjunction("or", modifier)

    def NOT(self, *, modifier=False):
        self._addConjunction("not", modifier)


    #
    # private helpers
    #

    def _findParent(self):
        conjN = self.etree.xpath("//s:and|//s:and|//s:or", namespaces=NSMAP)

        tree = etree.ElementTree(self.etree)
        if len(conjN) == 0:
            parentN = self.etree.xpath(
                "/s:application/s:modules/s:module/s:search/s:expert", namespaces=NSMAP
            )[0]
        else:
            amax = 0
            for eachN in conjN:
                epath = tree.getelementpath(eachN)
                alist = epath.split("/")
                if len(alist) >= amax:
                    amax = len(alist)
                    parentN = eachN
        #print("parentN" + tree.getelementpath(parentN))
        return parentN

    def _addConjunction(self, kind, modifier=False):
        """
        kind is either "and", "or" or "not"
        if modifier is True, new conjunction is added after the last;
        if modifier is False, it is a subelement
        """
        parentN = self._findParent()

        if modifier is False:
            etree.SubElement(
                parentN, "{http://www.zetcom.com/ria/ws/module/search}" + kind
            )
        else:
            conjN = etree.Element("{http://www.zetcom.com/ria/ws/module/search}" + kind)
            parentN.addnext(conjN)


if __name__ == "__main__":
    s = Search(module="Object")
    s.addCriterion(operator="equalsField", field="Object.ObjRegistrarRef.RegExhibitionRef.__id", value="20222")
    s.prints()
    s.validate(mode="search")
#    print(s.toString())
#    s.validate()
# s.addCriterion(operator="equalsField",field="__id", value="29825")
#    s.toFIle(path="search.xml")
#    s.validate()

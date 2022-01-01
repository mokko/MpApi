"""
Make the Search request in xml from scratch

Specification: http://docs.zetcom.com/ws/module/search/search.xml

Currently, we're making only expert searches.

We're using a different lingo here than Zetcom. For us an expert search can
contain different criteria. Criteria have three components
- a field (e.g. __id)
- an operator (e.g. isNull)
- and a value (e.g. 123)

With some operators, such as isNull, no value is needed/allowed.

Each criterion can be combined with others using the usual conjunctions (and, 
or, not). 

USAGE
    s = mpSearch(fromFile="path/to/file")
    s = mpSearch(fromString=xml)
    s = mpSearch(module="Object", limit=-1, offset=0)
    s.setParam(key="offset", value=123) # offset or limit
    s.AND()
    s.addCriterion(operator="equalsValue", field="__id", value="1234")
    s.addCriterion(operator="equalsValue", field="__id", value="1234")

    #if you only want certain fields back, list them
    s.addField("ObjExampleMissing")

#helpers
    print(s.toString())
    s.toFile(path="out.xml")
    s.validate(mode="search")
    
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
from lxml import etree  # type: ignore
from MpApi.Helper import Helper

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


class Search(Helper):
    def __init__(
        self, *, module=None, limit=-1, offset=0, fromFile=None, fromString=None
    ):
        """
        Currently, limit, offset and module are ignored if fromFile or fromString are used.
        """

        if fromString is not None:
            self.fromString(xml=fromString)
        elif fromFile is not None:
            self.etree = etree.parse(str(fromFile))
        else:
            if module is None:
                raise TypeError(
                    "Module is not allowed to be None when making search from string"
                )
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
            self.lastN = self.etree.xpath(
                "/s:application/s:modules/s:module/s:search/s:expert", namespaces=NSMAP
            )[0]

    def addCriterion(self, *, operator, field, value=None):
        if operator not in allowedOperators:
            raise TypeError(f"Unknown operator: '{operator}'")

        if value is None:
            etree.SubElement(
                self.lastN,
                "{http://www.zetcom.com/ria/ws/module/search}" + operator,
                fieldPath=field,
            )
        else:
            etree.SubElement(
                self.lastN,
                "{http://www.zetcom.com/ria/ws/module/search}" + operator,
                fieldPath=field,
                operand=value,
            )

    def addField(self, *, field):
        try:
            selectN = self.etree.xpath(
                "/s:application/s:modules/s:module/s:search/s:select", namespaces=NSMAP
            )[0]
        except:
            expertN = self.etree.xpath(
                "/s:application/s:modules/s:module/s:search/s:expert", namespaces=NSMAP
            )[0]
            selectN = etree.Element(
                "{http://www.zetcom.com/ria/ws/module/search}select"
            )
            expertN.addprevious(selectN)
        etree.SubElement(
            selectN,
            "{http://www.zetcom.com/ria/ws/module/search}field",
            fieldPath=field,
        )

    #
    # conjunctions
    #

    def AND(self):
        self._addConjunction(Type="and")

    def OR(self):
        self._addConjunction(Type="or")

    def NOT(self):
        self._addConjunction(Type="not")

    def setParam(self, *, key, value):
        """
        changes offset in the object; does not create a copy; does not return particularily much;
        """
        searchN = self.etree.xpath(
            "/s:application/s:modules/s:module/s:search", namespaces=NSMAP
        )[0]
        searchA = searchN.attrib
        searchA[key] = value

    #
    # private helpers
    #

    def _addConjunction(self, *, Type):
        """
        kind is "and", "or" or "not"
        either places conjunction under expert or under last conjunction that has been added.
        """
        allowed_types = ["and", "or", "not"]
        if Type not in allowed_types:
            raise TypeError("conjunction type NOT ALLOWED")

        self.lastN = etree.SubElement(
            self.lastN, "{http://www.zetcom.com/ria/ws/module/search}" + Type
        )


if __name__ == "__main__":
    s = Search(module="Object")
    s.addCriterion(
        operator="equalsField",
        field="Object.ObjRegistrarRef.RegExhibitionRef.__id",
        value="20222",
    )
    s.print()
    s.validate(mode="search")
#    print(s.toString())
#    s.validate()
# s.addCriterion(operator="equalsField",field="__id", value="29825")
#    s.toFIle(path="search.xml")
#    s.validate()

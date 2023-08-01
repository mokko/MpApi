"""
In this document, I try to answer the questions some of my colleagues have concerning the API
as good as I can
https://pad.sbb.spk-berlin.de/yBVQy8vaS0qupYpUgVHK7g
"""


from mpapi.search import Search
from mpapi.module import Module
from mpapi.client import MpApi
from mpapi.constants import get_credentials, parser, NSMAP
from lxml import etree

user, pw, baseURL = get_credentials()
client = MpApi(baseURL=baseURL, user=user, pw=pw)


def write_to_file(m, fn):
    print(f"writing to {fn}")
    m.toFile(path=fn)


def test_Suche_nach_ID():
    """
    Gegeben ist die eine Objekte-DS wie 739673. Die API soll den gesamten DS zurückgeben.
    """
    q = Search(module="Object")
    q.addCriterion(operator="equalsField", field="__id", value="739673")
    q.validate(mode="search")  # raises on error

    m = client.search2(query=q)
    assert m
    write_to_file(m, "Object739673.zml.xml")


def test_Objekte_nach_Titel():
    """
    Gegeben ist ein String. Gesucht werden alle Objekte-DS, die diesen String im Feld Titel.Titel enthalten.
    """

    q = Search(module="Object")
    q.addCriterion(
        operator="contains", field="ObjObjectTitleGrp.TitleTxt", value="Siamesische"
    )
    q.validate(mode="search")  # raises on error

    m = client.search2(query=q)
    assert len(m) > 4
    write_to_file(m, "ObjectTitel.zml.xml")


def test_Objekte_letzte_Änderung():
    """
    Gesucht werden alle Objekte, die seit bestimmtem Datum geändert wurden. Wir wollen
    nur die ersten 10 DS (limit), damit es nicht so lange dauert.
    """
    q = Search(module="Object", limit=10)
    q.addCriterion(operator="greater", field="__lastModified", value="2023-05-23")
    q.validate(mode="search")  # raises on error

    m = client.search2(query=q)
    assert len(m) > 4
    write_to_file(m, "ObjectLastmodifiedSince.zml.xml")


def test_freigegebene_Objekte():
    """
    Angezeigt werden sollen alle Objekte, die SMB-Digital Freigabe = Ja haben. Damit es
    nicht ewig dauert, laden wir nur die ersten 10 herunter.
    """

    q = Search(module="Object", limit=10)
    q.AND()
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # Daten freigegeben für SMB-digital
    )
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.PublicationVoc",
        value="1810139",  # Ja
    )
    q.validate(mode="search")  # raises on error
    # print (q.toString())
    m = Module()
    m = client.search2(query=q)
    assert len(m) > 4
    write_to_file(m, "freigegebeneObjekte.zml.xml")


def test_freigegebene_Objekte_IDs():
    """
    Alle Objekte die SMB-freigegeben sind, aber nur die IDs.
    """
    q = Search(module="Object", limit=1000)
    q.AND()
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # Daten freigegeben für SMB-digital
    )
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.PublicationVoc",
        value="1810139",  # Ja
    )
    q.addField(field="__id")
    q.validate(mode="search")  # raises on error
    m = client.search2(query=q)
    write_to_file(m, "freigegebeneObjekteIDs.zml.xml")
    assert len(m) == 1000


def test_freigegebene_Objekte_Attachments():
    """
    alle Objekte abrufen, die freigegeben sind (“Daten freigegeben für SMB-digital”) und
    Anhänge haben.

    Ich verstehe hier Anhang als das, was Zetcom Attachment nennt, also
        moduleItem/@hasAttachments = 'true'
    Diese Anhänge sind, glaube ich, das Standardbild.
    Diese Abfrage kann ich nicht direkt mit mpapi.search formulieren. Muss also erst alle
    Objekte abfragen und dann im XML nach attachment=true filtern. Das Ergebnis schreibe
    ich dann wie gewohnt in XML.
    """
    q = Search(module="Object", limit=100)
    q.AND()
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.TypeVoc",
        value="2600647",  # Daten freigegeben für SMB-digital
    )
    q.addCriterion(
        operator="equalsField",
        field="ObjPublicationGrp.PublicationVoc",
        value="1810139",  # Ja
    )
    q.addField(field="__id")
    q.validate(mode="search")  # raises on error
    m = client.search2(query=q)
    print(f"{len(m)}")
    resultL = m.xpath(
        "/m:application/m:modules/m:module/m:moduleItem[@hasAttachments = 'true']"
    )

    ET = etree.XML(
        """
    <application xmlns="http://www.zetcom.com/ria/ws/module">
        <modules>
            <module name="Object">
            </module>
        </modules>
    </application>""",
        parser=parser,
    )

    moduleN = ET.xpath("/m:application/m:modules/m:module", namespaces=NSMAP)[0]
    print(moduleN)

    [moduleN.append(resultN) for resultN in resultL]
    m = Module(tree=ET)
    m.updateTotalSize()

    write_to_file(m, "freigegebeneObjekteAnhänge.xml")
    # assert len(m) == 100


def test_multimedia_for_object():
    """
    alle Dateinamen für digitale Assets für ein Objekt abrufen.
    Ich nehme wieder das Object 739673
    """
    q = Search(module="Multimedia")
    q.addCriterion(operator="equalsField", field="MulObjectRef.__id", value="739673")
    q.addField(field="MulOriginalFileTxt")
    q.validate(mode="search")  # raises on error

    m = client.search2(query=q)
    assert m
    write_to_file(m, "Multimedia_for_Object739673.zml.xml")


def test_welche_module_und_felder():
    m = client.getDefinition2()
    write_to_file(m, "definition.xml")

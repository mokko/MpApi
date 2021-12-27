from MpApi.Search import Search
from MpApi.Module import Module


def test_load_file():
    m = Module(file="sdata/exhibit20222.xml")
    totalSize = m.totalSize(module="Multimedia")
    # print(totalSize)
    assert totalSize is not None
    for mi in m.iter():
        m.attribute(parent=mi, name="uuid", action="remove")
        m._dropUUID()
        # m._dropFields(parent=mi, type="virtualField")  # if no parent, assume self.etree
        # m._dropFields(parent=mi, type="systemField")  # if no parent, assume self.etree
    m.toFile(path="sdata/response-simplified.xml")
    assert m.validate() is True


def test_from_scratch():
    m = Module(name="Object")
    miN = m.moduleItem(hasAttachments="false")
    m.dataField(parent=miN, name="ObjTechnicalTermClb", value="Zupftrommel")
    vrN = m.vocabularyReference(
        parent=miN, name="ObjCategoryVoc", id="30349", instanceName="ObjCategoryVgr"
    )
    m.vocabularyReferenceItem(parent=vrN, id="3206642", name="Musikinstrument")
    rgN = m.repeatableGroup(parent=miN, name="ObjObjectNumberGrp", size="1")
    rgiN = m.repeatableGroupItem(parent=rgN, id="20414895")
    m.dataField(parent=rgiN, name="InventarNrSTxt", value="I C 7723")

    for miN in m.iter():
        m.print(miN)
    # m.print()
    assert m.validate() is True
    m.toFile(path="sdata/fromScratch.xml")


def test_totalSize():

    m = Module(file="sdata/exhibit20222.xml")
    assert m.totalSize(module="Object") is None
    assert m.totalSize(module="Multimedia") == 619

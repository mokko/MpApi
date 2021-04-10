# -*- coding: UTF-8
import sys
sys.path.append ("../src")
from Search import Search
from Module import Module

with open("../sdata/credentials.py") as f:
    exec(f.read())

def test_load_file():
    m = Module(file="sdata/exhibit20222.xml")
    totalSize = m.attribute(name="totalSize")
    print(totalSize)  # if no parent, assume self.etree
    assert totalSize is not None
    for mi in m.iter(): 
        m.attribute(parent=mi, name="uuid", action="remove")
        m._rmUuidsInReferenceItems(parent=mi)
        m._dropFields(
            parent=mi, type="virtualField"
        )  # if no parent, assume self.etree
        m._dropFields(
            parent=mi, type="systemField"
        )  # if no parent, assume self.etree
    m.toFile(path="../sdata/exhibitObjects/response-simplified.xml")
    m.validate()

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
    m.print()
    m.validate()
    m.toFile(path="fromScratch.xml")

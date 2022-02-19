# -*- coding: UTF-8
from mpapi.module import Module
from mpapi.sar import Sar

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_init():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    assert sr


# sar doesn't have getItem anymore


def test_getObjectSet():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    m = sr.getByExhibit(module="Object", Id="20222")
    assert m.actualSize(module="Object") > 0

    # r = sr.getByGroup(module="Object", Id="29002")
    # assert r.status_code == 200


def test_getMediaSet():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    m = sr.getByExhibit(module="Multimedia", Id="20222")
    m.toFile(path="../sdata/Exhibition20222.xml")
    assert m.actualSize(module="Multimedia") > 0

    m = sr.getByGroup(module="Object", Id="29002")
    assert m.actualSize(module="Object") > 0
    m.toFile(path="../sdata/group29002.xml")


# old version of saveAttachments required an xml document as string
# new version wants data as Module object
def test_saveAttachments():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    m = Module(file="../sdata/exhibit20222.xml")
    sr.saveAttachments(data=m, adir="../sdata")


def test_getByApprovalGrp():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    m = sr.getByApprovalGrp(Id="4460851", module="Object")  # 2600647 = SMB-Freigabe
    m.toFile(path="../sdata/getByApprovalGroup.xml")


def test_checkApproval():
    sr = Sar(baseURL=baseURL, user=user, pw=pw)
    b = sr.checkApproval(mtype="Object", ID=798706)
    print(f"checkApproval: {b}")
    assert b is False
    b = sr.checkApproval(mtype="Object", ID=255442)
    print(f"checkApproval: {b}")
    assert b is True

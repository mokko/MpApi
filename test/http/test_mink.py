from pathlib import Path
from mpapi.mink import Mink
from pathlib import Path

with open("../sdata/credentials.py") as f:
    exec(f.read())


def test_init():
    m = Mink(conf="../sdata/jobs.dsl", job=None, baseURL=baseURL, pw=pw, user=user)
    assert m


def test_getItem():
    m = Mink(conf="../sdata/jobs.dsl", job=None, baseURL=baseURL, pw=pw, user=user)
    assert m.project_dir == Path(".")
    xml = m.getItem(["Object", "739673"])  # 2609893
    assert isinstance(xml, str)
    assert xml.find("ä") != -1

    xml = m.getItem(["Object", "739673"])  # the second time it will come from disk
    assert xml.find("ä") != -1
    ET = m.xmlToEtree(xml=xml)
    print("ET" + str(ET))
    # assert type(ET)


def test_getObjects():
    m = Mink(conf="../sdata/jobs.dsl", job="HFWest", baseURL=baseURL, pw=pw, user=user)
    type = "exhibit"
    id = "20222"
    out = "ex20222"  # not a full filename
    xml = m.getObjects([type, id, out])
    assert xml.find("ä") != -1


def test_run_Test_job():
    m = Mink(conf="../sdata/jobs.dsl", job="Test", baseURL=baseURL, pw=pw, user=user)
    print(m)


def test_getReg():
    m = Mink(conf="../sdata/jobs.dsl", job="Test", baseURL=baseURL, pw=pw, user=user)
    m.getRegistry(["exhibit", "20222", "test"])

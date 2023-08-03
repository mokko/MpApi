from mpapi.vocabulary import Vocabulary


def test_init_from_file():
    v = Vocabulary(file="nodes-AccDenominationVgr.xml")
    assert v


def test_init_from_str():
    xml = """
<node xmlns="http://www.zetcom.com/ria/ws/vocabulary" logicalName="http://www.test/id/123456" id="5091855">
  <uuid>a1b8aaa5-c1e2-443e-b748-13a4f0d6ecf5</uuid>
  <version>2023-08-02T22:12:52.780Z</version>
  <lastModified>2023-08-02T22:12:52.639Z</lastModified>
  <lastModifiedUser>EM_MM</lastModifiedUser>
  <orgUnit logicalName="EMMedienarchiv"/>
  <status logicalName="refused"/>
  <parents>
    <parent nodeId="4913857"/>
  </parents>
  <instance logicalName="GenPlaceVgr" id="30288"/>
  <terms>
    <term id="5696815">
      <uuid>a8575727-8fde-4054-a432-09d7cd55de41</uuid>
      <version>2023-08-02T22:12:52.797Z</version>
      <isoLanguageCode>de</isoLanguageCode>
      <content>Test</content>
      <order>1</order>
      <note>Bemerkung</note>
      <status logicalName="valid"/>
      <category logicalName="preferred"/>
    </term>
  </terms>
  <comment>Bemerkung</comment>
  <relations>
    <relation nodeId="2284911" id="100275364">
      <uuid>341ba531-bf24-4081-94a2-066034bb8e23</uuid>
      <version>2023-08-02T22:12:52.780Z</version>
      <type>peer_to_peer</type>
      <direction>undirected</direction>
    </relation>
  </relations>
</node>
    """
    v = Vocabulary(xml=xml)
    assert v


def test_len():
    v = Vocabulary(file="nodes-AccDenominationVgr.xml")
    assert len(v) == 5


def test_iter():
    v = Vocabulary(file="nodes-AccDenominationVgr.xml")
    c = 0
    for node in v:
        c += 1
    assert c == 5


def test_validate():
    v = Vocabulary(file="nodes-AccDenominationVgr.xml")
    try:
        v.validate(mode="voc")
    except Exception as e:
        raise (e)
    assert True is True

from pathlib import Path
from MpApi.Client import MpApi
from MpApi.Module import Module

with open("sdata/vierteInstanz.py") as f:
    exec(f.read())

# first test is if i can manually change Freigabe of obj id 744767
# ok.

"""
<repeatableGroup name="ObjPublicationGrp" size="2">
  <repeatableGroupItem id="42625592">
    <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
      <vocabularyReferenceItem id="1810139" name="Ja">
        <formattedValue language="en">Ja</formattedValue>
      </vocabularyReferenceItem>
    </vocabularyReference>
    <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
      <vocabularyReferenceItem id="2600647" name="Daten freigegeben für SMB-digital">
        <formattedValue language="en">Daten freigegeben für SMB-digital</formattedValue>
      </vocabularyReferenceItem>
    </vocabularyReference>
  </repeatableGroupItem>
  <repeatableGroupItem id="49859597">
    <dataField dataType="Date" name="ModifiedDateDat">
      <value>2021-02-25</value>
      <formattedValue language="en">25/02/2021</formattedValue>
    </dataField>
    <dataField dataType="Varchar" name="ModifiedByTxt">
      <value>EM_JoFi</value>
    </dataField>
        <dataField dataType="Long" name="SortLnu">
      <value>1</value>
      <formattedValue language="en">1</formattedValue>
    </dataField>
    <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
      <vocabularyReferenceItem id="1810139" name="Ja">
        <formattedValue language="en">Ja</formattedValue>
      </vocabularyReferenceItem>
    </vocabularyReference>
    <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
      <vocabularyReferenceItem id="4460851" name="DatenFreigegebenfürEMBeninProjekt">
        <formattedValue language="en">Daten freigegeben für EM Benin-Projekt</formattedValue>
      </vocabularyReferenceItem>
    </vocabularyReference>
  </repeatableGroupItem>
</repeatableGroup>
"""

"""
Create repeatable group / reference
<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Address">
      <moduleItem id="29011">
        <repeatableGroup name="AdrContactGrp">
          <repeatableGroupItem>
            <dataField name="ValueTxt">
              <value>max_muster</value>
            </dataField>
            <vocabularyReference name="TypeVoc">
              <vocabularyReferenceItem id="30158" />
            </vocabularyReference>
          </repeatableGroupItem>
        </repeatableGroup>
      </moduleItem>
    </module>
  </modules>
</application>
"""


def test_init():
    api = MpApi(baseURL=baseURL, user=user, pw=pw)
    assert api
    r = api.getItem(module="Object", id="744767")
    print(r.status_code)
    assert r
    api.toFile(xml=r.text, path="sdata/744767.xml")
    xml = f"""
    <application xmlns="http://www.zetcom.com/ria/ws/module">
      <modules>
        <module name="Object">
          <moduleItem id="744767">
            <repeatableGroup name="ObjPublicationGrp">
                <repeatableGroupItem>
                    <dataField dataType="Date" name="ModifiedDateDat">
                        <value>2021-05-21</value>
                    </dataField>
                    <dataField dataType="Varchar" name="ModifiedByTxt">
                        <value>{user}</value>
                    </dataField>
                    <dataField dataType="Long" name="SortLnu">
                        <value>1</value>
                    </dataField>
                   <vocabularyReference name="PublicationVoc" id="62649" instanceName="ObjPublicationVgr">
                     <vocabularyReferenceItem id="1810139"/>
                   </vocabularyReference>
                   <vocabularyReference name="TypeVoc" id="62650" instanceName="ObjPublicationTypeVgr">
                     <vocabularyReferenceItem id="2600647"/>
                   </vocabularyReference>
               </repeatableGroupItem>
            </repeatableGroup>
          </moduleItem>
        </module>
      </modules>
    </application>"""
    m = Module(xml=xml)
    m.validate()
    # Might be stupid to create a Freigabe every time we run a test suite
    # r = api.createRepeatableGroup(
    #    module="Object", id="744767", repeatableGroup="ObjPublicationGrp", xml=xml
    # )
    # assert r
    print(r.status_code)

"""

EXPERIMENTAL / USE AT YOUR OWN RISK / UNTESTED

ObjectGroup: create, update, delete ObjectGroups as well as items in such groups.

For example: Download (get) an existing ObjectGroup record and save it locally/
internally. Then add new items to the existing ObjectGroup in RIA and update the 
new state locally/internal again.

Limitation of this class: it can only work with a single group (although the 
schema probably allows chaining multiple groups into one document).

I stands for internally
R stands for remote
N stands for a single etree/lxml node
L stands for a list of etree/lxml nodes 

USAGE:
    # working on whole group
    grp = ObjectGroup(grpId=123) # get an existing group from RIA
    grp = ObjectGroup() # start a new group from scratch
    m = grp.getI() # returns internal group as Module object 

    # todo - not yet implemented
    grp.mkGroupR() # tell RIA to create a whole new group using the internally saved record 
    grp.delR(grpId=123) # delete whole group in RIA; to do, no priority
    grp.updateR(grpId=123) # overwrite group with ID 123 in RIA with the one saved internally

    # create etree Nodes
    nodeN = grp.mkItemN(objId=123, sort=12) # sort is optional
    nodeL = [nodeN1, nodeN2] 

    # tests working on internal 
    # remote tests: get the remote group and check internally: is this viable?
    bool = grp.ifInGrpI(objId=123) # check if objId=123 is in internal group
    objIds = grp.ifListInGrpI(objIds=[123, 124, 125]) # similar, but for lists of ids

    # working on items
    grp.addItemsR(nodes=nodeL) # includes upload to RIA; should this function check if objIds are already included?

    # todo - not yet implemented
    grp.addItemsI(node=nodeN)  # to add multiple nodes, just repeat
    grp.changeItemR(node=nodeN) # does this work on multiple items in one go? Need to try before I promise things
    grp.changeItemI(node=nodeN) # we can extract objId from node 
        

"""
from lxml import etree  # type: ignore
from mpapi.client2 import Client2

# from mpapi.client import MpApi
from mpapi.search import Search
from mpapi.module import Module
from mpapi.constants import NSMAP


class ObjectGroup:
    def __init__(self, *, grpId=None) -> None:
        self.client = Client2(baseURL=baseURL, user=user, pw=pw)
        if grpId is not None:
            self.group = self.client.getItem(modType="ObjectGroup", modItemId=grpId)
            # as Module object
        else:
            self.group = Module()
            modulesN = self.group.xpath("/m:application/m:modules")
            etree.SubElement(modulesN, "m:module", {name: "ObjectGroup"}, nsmap=NSMAP)

    def getI(self) -> Module:
        return self.group

    #
    # mk ET Nodes
    #
    def mkItemN(self, *, objId, sort=None):
        """
        Create invidual moduleItems as a ET node.

        Untested.
        """
        moduleItemN = etree.Element(
            "m:moduleItem", {moduleItemId: str(objId)}, nsmap=NSMAP
        )
        if sort is not None:
            dataFieldN = etree.XML(
                """
                <dataField dataType="Long" name="SortLnu">
                  <value>{sort}</value>
                </dataField>
            """
            )
            mouleItemN.insert(0, dataFieldN)  # 0=index/position
        return moduleItemN

    #
    # test internal data
    #

    def ifInGrpI(self, *, objId: str) -> bool:
        """
        Test if an individual objIs is a member in the group. Returns True or False.

        We used to have a variant where accept a list of objIds and return a list of hits.
        """

        modType = "ObjectGroup"
        for objId in objIds:
            modRefItemL = self.group.xpath(
                f"""/module[
                @name='{modType}'
            ]/m:moduleItem/m:moduleReference[
                @name='OgrObjectRef'
            ]/m:moduleReferenceItem[
                @moduleItemId = '{objId}'
            ]"""
            )

            try:
                modRefItemL[0]
            except:
                return False
            else:
                return True
                # included.add(objId)
            # return included

    def ifListInGrpI(self, *, objIds: list) -> list:
        """
        For a given list of objIds, returns a list of objIds which are a members of the
        internal list.

        UNTESTED.
        """
        modType = "ObjectGroup"
        included = set()
        for objId in objIds:
            modRefItemL = self.group.xpath(
                f"""/module[
                @name='{modType}'
            ]/m:moduleItem/m:moduleReference[
                @name='OgrObjectRef'
            ]/m:moduleReferenceItem[
                @moduleItemId = '{objId}'
            ]"""
            )

            try:
                modRefItemL[0]
            except:
                pass
            else:
                included.add(objId)  # should we yield here?
                # Dont think I win a lot by yielding...
        return included

    #
    # update items
    #

    def addItemsR(self, *, grpId: int, objId: int):
        """
        This is the second attempt, where we get the full record, but only try to add
        one element, the moduleReference containing the list of objects in the group.

        I'm guessing we're changing data in place, like a reference.

        N.B. Parameter 'size' omitted since i dont know the size at this time.

        Todo: Test if given objId is already included or not.


        This method might become more generic:
        addMRefItem (mtype, mItemId, mRef, mRefId)
        addVRefItem (mtype, mItemId, mRef, mRefId)
        addRGrpItem (mtype, mItemId, mRef, mRefId)

        addGrpItem (mtype, mItemId, gtype, ref, refId)
        where gType is either moduleReference, vocabularyReference or repeatableGroup
        """
        rGrp = "OgrObjectRef"
        mtype = "ObjectGroup"

        xml = f"""<application xmlns="http://www.zetcom.com/ria/ws/module">
          <modules>
            <module name="{mtype}">
              <moduleItem id="{grpId}">
                <moduleReference name="{rGrp}" targetModule="Object" multiplicity="M:N">
                  <moduleReferenceItem moduleItemId="{objId}"/>
                </moduleReference>
              </moduleItem>
            </module>
          </modules>
        </application>"""

        r = self.client.createGrpItem2(
            mtype="ObjectGroup", ID=grpId, grpref=rGrp, xml=xml
        )
        return r

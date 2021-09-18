class Check: 
    def checkFreigabe(self, *, id, node):
        try:
            node.xpath(
                """m:repeatableGroup[
                    @name='ObjPublicationGrp']/m:repeatableGroupItem/m:vocabularyReference[
                    @name='TypeVoc']/m:vocabularyReferenceItem[
                    @id='2600647']/../../m:vocabularyReference[
                    @name='PublicationVoc']/m:vocabularyReferenceItem[
                    @name='Ja']
                """,
                namespaces=self.NSMAP,
            )[0]
        except IndexError:
            print("   no smbfreigabe yet")
            if self.act is True:
                print (f"\tSETTING smbfreigabe for {id}")
                self._smbfreigabe(id=id, sort=1)
        else:
            print("   smbfreigabe=Ja exists")

    def checkOnlineDescription (self, *, id, node, marker):
        """
            Check if onlineBeschreibung exists; if not add marker in first description.
            If it exists, check if first description has marker. If not, add it.
        """
        rGrp = node.xpath("m:repeatableGroup[@name='ObjTextOnlineGrp']",
            namespaces=self.NSMAP)

        if len(rGrp) > 0:
            #if multiple onlineBeschreibungen, we'll write ONLY in first
            #if somebody else changes order, we're screwed
            #so we look at all repeatableGroupItems
            print("   online description exists already")
            valueL = rGrp[0].xpath("m:repeatableGroupItem/m:dataField[@name='TextClb']/m:value", namespaces=self.NSMAP)
            
            #list comprehension?
            found = 0
            for value in valueL:
                if marker in value.text:    
                    found += 1
                    print ("\tfound marker, no change necessary")

            if found == 0:
                print ("   marker not in online desc, ADDING MY MARK")
                if self.act is True:
                    self.updateOnlineDescription(node=rGrp[0], id=id, marker=marker)
        else:
            print("   no online description yet, ADDING MY MARK")
            if self.act is True:
                xml = self.createOnlineDescription(objId=id) 
    def visibleActiveUsers(self):
        """
        Returns list of active users' emails that are visible to the user who logging in through 
        the api.
        
        Returns a Python list (and not a requests objects).
        """
        s = Search(module="User")
        s.addCriterion(field="UsrStatusBoo", operator="equalsField", value="True")
        s.validate(mode="search")
        r = self.search(xml=s.toString())
        tree = etree.fromstring(bytes(r.text, "UTF-8"))
        emailL = tree.xpath(
            "/m:application/m:modules/m:module[@name = 'User']/m:moduleItem/m:dataField[@name = 'UsrEmailTxt']/m:value",
            namespaces=NSMAP,
        )
        ls = []
        for emailN in emailL:
            if emailN.text != "@smb.spk-berlin.de":
                ls.append(emailN.text)
        return ls # "; ".join(ls)

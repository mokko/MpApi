"""
Trying out ways to update a moduleItem[@name='Object'] node so that the 
last modified datee gets updated. 

I dont want this file to run as part of the test suite, so I dont call 
it a test, although it's in the test directory.
"""

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}

ETparser = etree.XMLParser(remove_blank_text=True)

import argparse
import logging
from lxml import etree
import os
import sys

if "PYTHONPATH" in os.environ:
    sys.path.append(os.environ["PYTHONPATH"])

credentials = "emem1.py"  # in pwd    
        
#from MpApi.Module import Module
#from MpApi.Search import Search
from MpApi.Client import MpApi
#from MpApi.Sar import Sar


#first way
class Updater:
    def _init_(self):
        with open(credentials) as f:
            exec(f.read())
        self.api = MpApi(baseURL=baseURL, user=user, pw=pw)


    def update1 (self, objId, module):
        r = self.api.getItem(module=module, id=objId)
        print (r.text)
        self.api.updateItem(module=module, id=objId, xml=r.text) #r.text.encode()
        """
        works but updates a set of fields and I am not sure if it is transparent which
        fields. 
        """

    def update2 (
        """
        Next attempt: I am trying to update a field which is rarely updated, like 
        VerwaltendeInstitution or Objettyp. Also, I am trying to update it with
        the identical value.
        """

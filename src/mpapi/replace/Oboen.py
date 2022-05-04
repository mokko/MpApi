import datetime
from mpapi.search import Search
from mpapi.replace.BoxerAufstand import BoxerAufstand

"""
Set SMBFreigabe for all objects in group with id 117396

First filter for objects in the group that are not yet approved (freigegeben),
then work on the not approved object.
"""


class Oboen(BoxerAufstand):
    def Input(self):
        r = {
            "Oboen": "184398",
        }
        return r
        

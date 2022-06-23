import datetime
from mpapi.search import Search
from mpapi.replace.FreigabeAndrea import FreigabeAndrea

# Does approval for all objects in a group


class FreigabeBenin(FreigabeAndrea):
    def Input(self):
        groups = {  # unsere Gruppe
            "Beninbronzen": "261396",
        }
        return groups

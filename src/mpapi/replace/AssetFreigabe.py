"""
Anna wants to SMB-approve practically all fotos by two photographers of the AKu

Fotografen:
look for assets
- of the whole AKu (excluding Fremdbesitz)
- only subset that has urheber/fotograf Jürgen Liepe OR Jörg von Bruchhausen
- only assets that dont have SMB-Freigabe yet
do
- set SMBFreigabe for those assets

AKu-Archiv OAK -> AKuArchivOAK
AKu-Archiv SSOZ -> AKuArchivSSOZ
AKu-Fotoarchiv -> AKuFotoarchiv
AKu-Kriegsverluste OAK -> AKuKriegsverlusteOAK
AKu-Kriegsverluste SSOZ -> AKuKriegsverlusteSSOZ
AKu-Süd-, Südost- und Zentralasien AKuSudSudostundZentralasien
AKu-Ostasiatische Kunst -> AKuOstasiatischeKunst

excluded
AKu-Fremdbesitz
AKu-Primärverpackungen
"""

import datetime

from mpapi.search import Search
from mpapi.replace.DigiP import DigiP


class AssetFreigabe(DigiP):
    def Input(self):
        return {"nothing": "yet"}

    def search(self, Id, limit=-1):
        query = Search(module="Multimedia", limit=limit)
        query.AND()
        # 3rd criteria
        # query.AND()
        query.addCriterion(
            operator="notEqualsField",  # equalsTerm
            field="MulApprovalGrp.TypeVoc",  # ObjCurrentLocationVoc
            value="1816002",  # using vocId SMB-Digital = 1816002
        )

        # 2nd criteria
        query.OR()
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="MulPhotographerPerRef",
            value="310973",  # Jürgen Liepe
        )
        query.addCriterion(
            operator="equalsField",  # notEqualsTerm
            field="MulPhotographerPerRef",
            value="400181",  # JvB
        )
        query.endConjunction()

        # 1st criteria
        query.OR()
        AKuList = [
            "AKuArchivOAK",
            "AKuArchivSSOZ",
            #    "AKuFotoarchiv", hat keinen J. Liepe und keinen J. von Bhausen
            "AKuKriegsverlusteOAK",
            "AKuKriegsverlusteSSOZ",
            "AKuSudSudostundZentralasien",
            "AKuOstasiatischeKunst",
        ]
        for orgUnit in AKuList:
            query.addCriterion(
                operator="equalsField",  # notEqualsTerm
                field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
                value=orgUnit,
            )

        # print(query.toFile(path="query.xml"))
        query.validate(mode="search")
        return query

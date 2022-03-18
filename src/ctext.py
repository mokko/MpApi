"""

Import C-Texts to RIA. This will be a two-step process.
(1) We parse A. Schäfer's Excel sheets (one at a time) and write the required
    info into a new Excel file sanitizing it somewhat on the way; in this step 
    we also look up the objIds from RIA plus possibly other information.
(2) we manually proof-reading the new Excel and potentially correct it    
(3) we upload the new Excel

Let's find good names 
(A) for the products: 
- A.Schäfer's Excel files are the original Excels
- The Excel sheets that I create are the proofing files; the rewritten Excel

(B) for the stages:
- initial conversion
- manual proofing
- upload to RIA

USAGE
    ctext --input original.xslx --output m39-rewrite.xslx  # step 1
    ctext --upload m39-rewrite.xslx  # step 3
"""

import argparse
from mpapi.search import Search
from mpapi.client import MpApi
from mpapi.module import Module
import openpyxl
from openpyxl import load_workbook, Workbook
from openpyxl.styles import NamedStyle, Alignment, Font

with open("credentials.py") as f:
    exec(f.read())


class Ctext:
    def __init__(self, *, user, pw, baseURL) -> None:
        self.client = MpApi(baseURL=baseURL, user=user, pw=pw)

    def _ingestSheet(self, sheet) -> None:
        """
        Read in orignal Excel and prepare sheet for rewrite Excel
        EXPECTS
        - sheet

        RETURNS
        - nothing; side-effect: self.ws2
        """
        print(f"*max row: {self.ws2.max_row}")  # 1-based
        ws2 = self.ws2
        new_row = ws2.max_row
        rno = 11  # 1-based
        for old_row in sheet.iter_rows(min_row=12, max_col=30):
            rno += 1
            new_row += 1
            identNrXLS = str(sheet[f"E{rno}"].value).strip()
            if identNrXLS == "./.":
                break  # are neglecting information in the rest of the line?

            print(f"\n***{new_row} identNr {identNrXLS}")

            # mapping original Excel fields to internal fields
            zeichen = sheet[f"W{rno}"].value
            künstler_de = sheet[f"o{rno}"].value
            künstler_en = sheet[f"p{rno}"].value
            titel_de = sheet[f"q{rno}"].value
            titel_en = sheet[f"r{rno}"].value
            kennung_de = sheet[f"U{rno}"].value
            kennung_en = sheet[f"V{rno}"].value

            # character translations: strange bullets
            mt = str.maketrans("#", "\u00B7")  # U+00B7 2022
            kennung_de = kennung_de.translate(mt)
            kennung_en = kennung_en.translate(mt)

            # DEBUGGING
            print(f"z {zeichen}")
            print(f"kü {künstler_de} || {künstler_en}")
            print(f"ti {titel_de} || {titel_en}")
            print(f"ke {kennung_de}")
            print(f"ke {kennung_en}")

            # deal with None and join fields
            de = ""
            if zeichen is not None:
                de += zeichen
            if künstler_de is not None and künstler_de != "./.":
                de += f"\n{künstler_de}"
            if titel_de is not None:
                de += f"\n\n{titel_de}"
            if kennung_de is not None:
                de += f"\n\n{kennung_de}"

            en = ""
            if zeichen is not None:
                en += zeichen
            if künstler_en is not None and künstler_en != "./.":
                en += f"\n{künstler_en}"
            if titel_en is not None:
                en += f"\n\n{titel_en}"
            if kennung_en is not None:
                en += f"\n\n{kennung_en}"

            de_html = "<html>"
            if zeichen is not None:
                de_html += zeichen.strip() + "<br/>"
            if künstler_de is not None and künstler_de != "./.":
                de_html += künstler_de.strip() + "<br/>"
            if titel_de is not None:
                de_html += f"<p><b>{titel_de.strip()}</b></p>"
            if kennung_de is not None:
                de_html += f"<p>{kennung_de.strip()}</p>"
            de_html += "</html>"

            en_html = "<html>"
            if zeichen is not None:
                en_html += zeichen.strip() + "<br/>"
            if künstler_en is not None and künstler_en != "./.":
                en_html += künstler_en.strip() + "<br/>"
            if titel_en is not None:
                en_html += f"<p><b>{titel_en.strip()}</b></p>"
            if kennung_de is not None:
                en_html += f"<p>{kennung_en.strip()}</p>"
            en_html += "</html>"

            # mapping internal fields to new Excel fields
            ws2[f"C{new_row}"] = identNrXLS
            ws2[f"D{new_row}"] = de
            ws2[f"E{new_row}"] = en
            ws2[f"F{new_row}"] = sheet[f"B{rno}"].value  # element
            ws2[f"G{new_row}"] = sheet.title  # Blatt
            ws2[f"H{new_row}"] = self.Input  # Datei
            ws2[f"I{new_row}"] = de_html
            ws2[f"J{new_row}"] = en_html

            ws2[f"D{new_row}"].style = "wrap"
            ws2[f"E{new_row}"].style = "wrap"
            ws2[f"I{new_row}"].style = "wrap"
            ws2[f"J{new_row}"].style = "wrap"

            # if new_row > 6:
            #    raise TypeError ("Let's stop here!")

    def _initProof(self) -> None:
        """
        Initialize rewrite Excel (self.ws2).
        """
        self.wb2 = Workbook(encoding="utf8")  # new (proof)
        ws2 = self.wb2.active
        self.ws2 = ws2
        ws2["A1"] = "objId(RIA)"
        ws2["B1"] = "IdentNr(RIA)"
        ws2["C1"] = "IdentNr(xlsx)"
        ws2["D1"] = "C-Text de"
        ws2["E1"] = "C-Text en"
        ws2["F1"] = "Element"
        ws2["G1"] = "Blatt"
        ws2["H1"] = "Datei"
        ws2["I1"] = "de_html"
        ws2["J1"] = "en_html"

        ns = NamedStyle(name="wrap")
        ns.alignment = Alignment(vertical="top", wrap_text=True)
        self.wb2.add_named_style(ns)

        ws2.column_dimensions["D"].width = 45
        ws2.column_dimensions["E"].width = 45
        ws2.column_dimensions["I"].width = 45
        ws2.column_dimensions["J"].width = 45

    def ingest(self, *, Input, output) -> None:
        """
        Rewrite original Excel file and save as output

        Expects
        - Input: original Excel file
        - output: path for rewritten output filename
        """
        wb1 = load_workbook(Input, encoding="utf8")  # original
        self.Input = Input
        self._initProof()
        if output is None:
            raise ValueError("Error: No output specified!")

        # should write multiple sheets from origin into one sheet at proofing stLooage
        for sheet in wb1:
            if sheet.title != "Info zur Datei":
                self._ingestSheet(sheet)
        openpyxl.writer.excel.save_workbook(self.wb2, output)

    def riaLookup(self, *, proof=None) -> None:
        """
        For every identNr from Excel, look up objId and IdentNr from RIA
        and write the results back to the proofing Excel (self.ws2).
        """
        if proof is not None:
            self.wb2 = load_workbook(proof)
            self.ws2 = self.wb2.active
            output = proof

        ws2 = self.ws2
        max_row = self.ws2.max_row
        print("*Entering ria lookup")
        print(f"**max row: {max_row}")  # 1-based

        for rno in range(2, max_row + 1):
            riaObjId = ws2[f"A{rno}"].value
            xslIdentNr = ws2[f"C{rno}"].value
            if riaObjId is None:
                newID = self._lookup(identNr=xslIdentNr, limit=1)
                if newID is not None:
                    ws2[f"A{rno}"] = newID
                    openpyxl.writer.excel.save_workbook(self.wb2, output)
                print(f"***row #{rno} {riaObjId} {xslIdentNr} -> {newID}")

        # openpyxl.writer.excel.save_workbook(self.wb2, output)

    def _lookup(self, *, identNr, limit=-1):
        """
        Some unicode/latin-1 mess is happening here...

        UnicodeEncodeError: 'latin-1' codec can't encode character '\u2014' in
        position 453: Body ('—') is not valid Latin-1. Use body.encode('utf-8')
        if you want to send it encoded in UTF-8.
        """

        print(f"-----------LOOKING UP objId for identNr {identNr}")
        q = Search(module="Object", limit=limit)
        q.AND()
        q.addCriterion(
            operator="equalsField",
            field="ObjObjectNumberVrt",  # ObjObjectNumberVrt
            value=identNr,
        )
        q.OR()
        AKuList = [
            "AKuArchivOAK",
            "AKuArchivSSOZ",
            #    "AKuFotoarchiv",
            "AKuKriegsverlusteOAK",
            "AKuKriegsverlusteSSOZ",
            "AKuSudSudostundZentralasien",
            "AKuOstasiatischeKunst",
        ]
        for orgUnit in AKuList:
            q.addCriterion(
                operator="equalsField",  # notEqualsTerm
                field="__orgUnit",  # __orgUnit is not allowed in Zetcom's own search.xsd
                value=orgUnit,
            )
        q.addField(field="__id")
        q.validate(mode="search")
        # print(q.toString())
        m = self.client.search2(query=q)
        # print (m.toString())
        size = m.actualSize(module="Object")
        if size == 1:
            try:
                newID = m.xpath(
                    "/m:application/m:modules/m:module[@name = 'Object']/m:moduleItem/@id"
                )[0]
            except:
                newID = None
        else:
            print(f"WARN: multiple or zero results {size}")
            newID = None
        # print (f"newID: {newID}")
        return newID

    def upload(self, *, Input) -> None:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload c-texts in two steps")
    parser.add_argument("-i", "--input", help="path to Excel input file")
    parser.add_argument("-o", "--output", help="path to new Excel (proofs)")
    parser.add_argument("-l", "--lookup", help="path to proofing Excel")
    parser.add_argument("-u", "--upload", help="path to new Excel for upload")
    args = parser.parse_args()

    ct = Ctext(user=user, pw=pw, baseURL=baseURL)
    if args.input is not None:
        ct.ingest(Input=args.input, output=args.output)
        ct.riaLookup(proof=args.output)

    if args.lookup:
        ct.riaLookup(proof=args.lookup)

    if args.upload is not None:
        ct.upload(Input=args.upload)

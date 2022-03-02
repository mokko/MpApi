"""

Import C-Texts to RIA. This will be a two-step process.
(1) We parse Anna Schäfer's Excel sheet, write the required info into a new 
    Excel file; in this step we also look up the objIds from RIA plus possibly
    other information. 
(2) After manually proof-reading the new Excel, we can upload the C-Texts

USAGE
    ctext -i excel.xslx -o m39.xslx  # step 1
    ctext -u m39.xslx  # step 2

"""

import argparse
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
        print(f"max row: {self.ws2.max_row}")  # 1-based
        ws2 = self.ws2
        new_row = ws2.max_row
        rno = 11  # 1-based
        for old_row in sheet.iter_rows(min_row=12, max_col=30):
            rno += 1
            new_row += 1
            identNrXLS = str(sheet[f"E{rno}"].value).strip()
            if identNrXLS == "./.":
                break

            künstler_de = sheet[f"o{rno}"].value
            künstler_en = sheet[f"p{rno}"].value
            titel_de = sheet[f"q{rno}"].value
            titel_en = sheet[f"r{rno}"].value
            kennung_de = sheet[f"U{rno}"].value
            kennung_en = sheet[f"V{rno}"].value
            zeichen = sheet[f"W{rno}"].value

            mt = str.maketrans("#", "\u00B7")  # U+00B7 2022

            de = f"{zeichen}\n\n{titel_de}\n\n{kennung_de}".translate(mt)
            en = f"{zeichen}\n\n{titel_en}\n\n{kennung_en}".translate(mt)

            ws2[f"C{new_row}"] = identNrXLS  # ident xls
            ws2[f"D{new_row}"] = de  # de
            ws2[f"E{new_row}"] = en  # en
            ws2[f"F{new_row}"] = sheet[f"B{rno}"].value  # element
            ws2[f"G{new_row}"] = sheet.title  # Blatt
            ws2[f"H{new_row}"] = self.Input  # Datei
            print(f" {new_row} {identNrXLS}")

            ws2[f"D{new_row}"].style = "wrap"
            ws2[f"E{new_row}"].style = "wrap"

    def _initProof(self) -> None:
        self.wb2 = Workbook()  # new (proof)
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

        ns = NamedStyle(name="wrap")
        ns.alignment = Alignment(vertical="top", wrap_text=True)
        self.wb2.add_named_style(ns)

        ws2.column_dimensions["D"].width = 45
        ws2.column_dimensions["E"].width = 45

    def ingest(self, *, Input, output) -> None:
        wb1 = load_workbook(Input)  # original
        self.Input = Input
        self._initProof()
        if output is None:
            raise ValueError("Error: No output specified!")
        for sheet in wb1:
            if sheet.title != "Info zur Datei":
                self._ingestSheet(sheet)
        openpyxl.writer.excel.save_workbook(self.wb2, output)

    def upload(self, *, Input) -> None:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload c-texts in two steps")
    parser.add_argument("-i", "--input", help="path to Excel input file")
    parser.add_argument("-o", "--output", help="path to new Excel (proofs)")
    parser.add_argument("-u", "--upload", help="path to new Excel for upload")
    args = parser.parse_args()

    ct = Ctext(user=user, pw=pw, baseURL=baseURL)
    if args.input is not None:
        ct.ingest(Input=args.input, output=args.output)
    if args.upload is not None:
        ct.upload(Input=args.upload)

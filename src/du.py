"""
du - download/upload allows downloading data from MuseumPlus to an excel sheet
and uploading it back after changes have been made to the excel 

THIS IS THE FIRST PROTOTYPE

WORKFLOW
1. You prepare a Excel sheet, e.g. using RIA.
2. You use du to fill the fields of the Excel with content from RIA
3. You make manual changes to the Excel sheet
4. You upload the changes to the RIA using du

FORMAT OF THE EXCEL FILE
Object Fieldname1 Fieldname2 ...
123456
123347

The excel format in words: 
* The column A contains RIA's IDs, except in A1 provides the respective module,
  e.g. Object.
* You may also list respective IdentNr in the second row for your orientation.
* The rest of the first row should be the fieldnames you want to download. You
  should use the internal fieldnames (probably using a special notation which
  is not determined yet.)
* at this point du works only the first Excel sheet, but this may change in the
  future.     

COMMAND LINE INTERFACE (subject to change)
    du -c down -i path/to/example.xlsx  # changes Excel so backup frequently
    du -c up -i path/to/example.xlsx

Known Limitations
* only accepts *.xlsx format, not *.xls -> Reformat using Excel
* If Excel file is still opened in Excel, it is locked and this script can't 
  run (Permission denied). -> Close Excel
"""

import argparse  # will disappear when code moved to __init__

# from mpapi.client import MpApi
from mpapi.sar import Sar
from mpapi.module import Module
from mpapi.search import Search
from openpyxl import load_workbook  # Workbook,

# from openpyxl.styles import PatternFill, colors, Fill
import openpyxl
from openpyxl.styles import Font
from openpyxl.styles.colors import Color

NSMAP = {
    "s": "http://www.zetcom.com/ria/ws/module/search",
    "m": "http://www.zetcom.com/ria/ws/module",
}


class Du:
    def __init__(
        self, *, cmd: str, Input: str, baseURL: str, user: str, pw: str
    ) -> None:
        self.sar = Sar(baseURL=baseURL, user=user, pw=pw)
        self.Input = Input
        self.wb = load_workbook(filename=Input)
        if cmd == "down":
            self.down()
        elif cmd == "up":
            self.up()
        else:
            raise ValueError(f"ERROR: Unknown command ´{cmd}´")
        self.wb.save(Input)  # overwriting original excel

    def down(self) -> None:
        """
        Given a properly prepared Excel sheet, du will fill in the requested
        data from RIA

        Expects
        * data in self.wb (side effect)

        Returns
        * nothing, but writes to self.wb (side effect)

        Decisions
        * Requires one or more queries to RIA? Let's try with one first.
        * At this stage we will be aggressively writing file caches for
          everything for debugging purposes

        Steps
        * we parse the first row looking for fields that need filling in
        * we create a query, save it, execute it
        * we receive the response and save it
        * we use the response to fill in the requested data
        """

        ws = self.wb.active  # should always activate first sheet

        known_modules = ["Object", "Person", "Multimedia"]

        A1 = ws["A1"].value  # could also be called mtype
        if A1 not in known_modules:
            raise ValueError(f"Error: A1 is not a known module ´{A1}´")

        query = Search(module=A1)
        if ws.max_row > 2:
            query.OR()
        for col in ws.iter_cols(min_row=2, max_col=1):
            for cell in col:
                print(f"{cell.row} {A1} {cell.value}")
                query.addCriterion(
                    operator="equalsField", field="__id", value=str(cell.value)
                )

        # at the moment, we're only working on cols from the Excel which start with dataField
        # later we need to search for these fields in the response and
        # write into exactly those columns, so we could remember the fields we picked
        requested = dict()  # requestedFields
        {
            1: {  # colNo as int, 1-based
                "field": "ObjTechnicalTermClb",  # aka zcName
                "full": "dataField.ObjTechnicalTermClb",
                "param": "value",
            }
        }
        for row in ws.iter_rows(min_col=2, max_row=1):
            for cell in row:
                if cell.value.startswith("dataField"):
                    field = cell.value.split(".", maxsplit=1)[1]
                    requested[cell.column] = {
                        "field": field,
                        "full": cell.value,
                    }
                    print(f"field {cell.column} {field}")
                    query.addField(field=field)

        query.validate(mode="search")
        query.toFile(path="query.debug.xml")
        print("Executing query...")
        m = self.sar.search(query=query)
        m.toFile(path="response.debug.xml")

        print(requested)

        for colNo in requested:
            print(f"FF {colNo}")
            for item in m.iter(module=A1):
                ID = int(item.xpath("@id")[0])
                field = requested[colNo]["field"]
                value = item.xpath(
                    f"m:dataField[@name = '{field}']/m:value/text()", namespaces=NSMAP
                )[0]
                self.fillIn(ID=ID, value=value, colNo=colNo)

    def fillIn(self, *, ID: int, value: str, colNo: int) -> None:
        """
        For given ID write value {value} to column no {colNo}
        """
        ws = self.wb.active  # should always activate first sheet
        print(f"filling in {ID} {value} into column no {colNo}")

        # we're calling "A4" a cell name

        colL = openpyxl.utils.cell.get_column_letter(colNo)
        rno = self._rowById(ID=ID)
        cname = f"{colL}{rno}"
        ws[cname] = value
        ws[cname].font = Font(color="005655")

    def _rowById(self, *, ID: int) -> int:
        ws = self.wb.active  # should always activate first sheet
        for col in ws.iter_cols(min_row=2, min_col=1, max_col=1):
            for cell in col:
                if cell.value == ID:
                    return cell.row

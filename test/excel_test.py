#!/usr/bin/env ipy
#

import operator
import os
import sys
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from excel import *
from test_utils import *


class RangeNameUnitTest(unittest.TestCase):

    def test_digiseq(self):
        self.assertEqual(digiseq(0,26), (0,))
        self.assertEqual(digiseq(1,26), (1,))
        self.assertEqual(digiseq(26,26), (1,0))

    def test_colname(self):
        self.assertEqual(colname(1), ("A"))
        self.assertEqual(colname(26), ("Z"))
        self.assertEqual(colname(27), ("AA"))

    def test_colval(self):
        self.assertEqual(colval("A"), (1))
        self.assertEqual(colval("Z"), (26))
        self.assertEqual(colval("AA"), (27))

    def test_colvalname(self):
        self.assertEqual(colname(colval("ABCDEFGHIJK")), "ABCDEFGHIJK")
        self.assertEqual(colval(colname(1234567890)), 1234567890)

    def test_cellname(self):
        self.assertEqual(cellname(1,1), "A1")
        self.assertEqual(cellname(1,27), "AA1")

class ExcelWorkbooksUnitTest(unittest.TestCase):

    def test_create(self):
        filename = getTestFileName("test_create.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        wb.Close()
        self.assertTrue(os.path.isfile(filename))

    def test_open(self):
        filename = getTestFileName("test_open.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        wb.Close()
        self.assertTrue(os.path.isfile(filename))

        wb = ExcelApplication().Workbooks(filename)
        wb.Close()
        self.assertTrue(os.path.isfile(filename))

    def test_multi_open(self):
        filename1 = getTestFileName("test_multi1.xlsx")
        filename2 = getTestFileName("test_multi2.xlsx")
        filename3 = getTestFileName("test_multi3.xlsx")
        filename4 = getTestFileName("test_multi4.xlsx")

        wb1 = ExcelApplication().Workbooks(filename1)
        wb2 = ExcelApplication().Workbooks(filename2)
        wb3 = ExcelApplication().Workbooks(filename3)
        wb4 = ExcelApplication().Workbooks(filename4)

        wb1.Close()
        wb2.Close()
        wb3.Close()
        wb4.Close()

        self.assertTrue(os.path.isfile(filename1))
        self.assertTrue(os.path.isfile(filename2))
        self.assertTrue(os.path.isfile(filename3))
        self.assertTrue(os.path.isfile(filename4))


class ExcelWorksheetsUnitTest(unittest.TestCase):

    def test_create(self):
        filename = getTestFileName("test_worksheet_create.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        wsheets = wb.Worksheets
        self.assertEqual(wsheets.Count, 3)

        ws = wsheets.create('test')
        self.assertEqual(wsheets.Count, 4)

        wb.Close()


    def test_multi_create(self):
        filename = getTestFileName("test_worksheet_create.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        wsheets = wb.Worksheets
        self.assertEqual(wsheets.Count, 3)

        ws = wsheets.create('test')
        self.assertEqual(wsheets.Count, 4)

        wb.Save()

        wb = ExcelApplication().Workbooks(filename)
        wsheets = wb.Worksheets
        self.assertEqual(wsheets.Count, 4)

        ws = wsheets.create('test1')
        self.assertEqual(wsheets.Count, 5)

        wb.Close()


class ExcelWorksheetUnitTest(unittest.TestCase):

    def test_UsedRange(self):
        filename = getTestFileName("test_used_range.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        ws = wb.Worksheets('test')

        ws.Cells(2,3).text = "hello"
        self.assertEqual(ws.Cells(2,3).text, "hello")

        ws.Cells(11,22).text = "world"

        rng = ws.UsedRange
        self.assertEqual(rng.Row, 2)
        self.assertEqual(rng.Column, 3)

        print("Rows: ", rng.Rows.Count)
        print("Columns: ", rng.Columns.Count)

        wb.Close()


    def _Cells(self):
        ws = ExcelApplication().Workbooks('test\\test1.xlsx').Worksheets('test1')
        cell = ws.Cells(4,3)
        
        self.assertEqual(cell.Row, 4)
        self.assertEqual(cell.Column, 3)
        self.assertEqual(cell.Rows.Count, 1)
        self.assertEqual(cell.Columns.Count, 1)


    def _CellValue(self):
        rng = ExcelApplication().Workbooks('test\\test1.xlsx').Worksheets('test1').UsedRange

        cell = rng.Cells(1,1)
        self.assertEqual(cell.text, "TopLeft")

        cell = rng.Cells(rng.Rows.Count, rng.Columns.Count)
        self.assertEqual(cell.text, "BottomRight")

        cell = rng.Cells(1, rng.Columns.Count)
        cell.text = "TopRight"
        self.assertEqual(cell.text, "TopRight")
        cell.value = None
        self.assertEqual(cell.text, "")

    def _Row_Column(self):
        col = ExcelApplication().Workbooks('test\\test1.xlsx').Worksheets('test1').UsedRange.Columns

    
########################################################################
# Main
########################################################################

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main(verbosity=2)

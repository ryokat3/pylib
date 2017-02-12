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

        wb = ExcelApplication().Workbooks.open(filename)
        wb.Close()
        self.assertTrue(os.path.isfile(filename))


class ExcelWorksheetsUnitTest(unittest.TestCase):

    def test_create(self):
        filename = getTestFileName("test_worksheet_create.xlsx")

        wb = ExcelApplication().Workbooks(filename)
        wsheets = wb.Worksheets
        self.assertEqual(wsheets.Count, 3)

        ws = wsheets.create('test')
        self.assertEqual(wsheets.Count, 4)

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

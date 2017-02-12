#!/usr/bin/env ipy
#

import operator
import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from excel import *


class ExcelWorkbooksUnitTest(unittest.TestCase):

    def test_create(self):
        filename = 'test1.xlsx'

        self.assertFalse(os.path.isfile(filename))
        wb = ExcelApplication().Workbooks(filename)
        self.assertTrue(os.path.isfile(filename))
        del wb
        os.remove(filename)
        self.assertFalse(os.path.isfile(filename))
    

class ExcelWorksheet_UnitTest(unittest.TestCase):

    def _UsedRange(self):
        rng = ExcelApplication().Workbooks('test\\test1.xlsx').Worksheets('test1').UsedRange
        cell = rng.Cells(1,1)
        
        self.assertEqual(rng.Row, cell.Row)
        self.assertEqual(rng.Column, cell.Column)
        self.assertEqual(rng.Rows.Count, 8)
        self.assertEqual(rng.Columns.Count, 4)
        self.assertEqual(cell.Rows.Count, 1)
        self.assertEqual(cell.Columns.Count, 1)

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

#!/usr/bin/env ipy.exe
# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8:
#
#          Don't use 'fenc' instead of 'fileencoding' !!
#          Python also interprets this line !!
#

import clr
clr.AddReference('office')
clr.AddReference('Microsoft.Office.Interop.Excel')
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('System.Xml')

import System
from System import Enum
from System import DateTime
from System.Drawing.Imaging import ImageFormat
from System.IO import MemoryStream
from System.IO import TextReader
from System.IO import FileInfo
from System.Runtime.InteropServices import Marshal
from System.Runtime.InteropServices import COMException
from System.Reflection import Missing
from System.Windows.Forms import Clipboard
from System.Windows.Forms import DataFormats
from System.Xml import XmlDocument
from System.Xml import XmlReader
from System.Xml import XmlNamespaceManager

from Microsoft.Office.Core import *
from Microsoft.Office.Interop.Excel import *

import atexit
import functools
import itertools
import logging
import os
import re
import shutil
import sys

from itertools import chain
from itertools import ifilter
from itertools import imap
from itertools import izip

########################################################################
# Common
########################################################################

def FullName(path):
    return FileInfo(path).FullName


def ExcelFileFormat(path):
    return XlFileFormat.xlOpenXMLWorkbook \
        if os.path.splitext(path)[1] != ".xls" else \
           XlFileFormat.xlWorkbookNormal


def excel_suppress_alert_dialog(app, func):
    display_alerts_value = app.DisplayAlerts
    app.DisplayAlerts = False
    func()
    app.DisplayAlerts = display_alerts_value


def atexit_register(func, text=None):
    def _(func):
        try:
            func()
        except Exception:
            if text != None:
                logging.info("{0}: {1}".format(funcname(), text))
            traceback.print_exc()
    return atexit.register(lambda: _(func))


########################################################################
# Com Object Base
########################################################################

class ComObject(object):
    
    def __init__(self, com, parent):
        logging.debug("{0}.__init__".format(self.__class__.__name__))

        self._com = com
        self._parent = parent
        
    def __del__(self):
        self._parent = None
        if self._com is not None:
            Marshal.ReleaseComObject(self._com)
            self._com = None
        logging.debug("{0}.__del__".format(self.__class__.__name__))

    def find_ancestor(self, cls):
        parent = self
        while parent != None and type(parent) != cls:
            parent = parent._parent
        return parent            
    
    @property
    def Application(self):
        return self.find_ancestor(ExcelApplication)

    
class WorksheetComObject(ComObject):
    
    def __init__(self, com, parent):
        super(WorksheetComObject, self).__init__(com, parent)

    def __del__(self):
        super(WorksheetComObject, self).__del__()
        
    @property
    def Worksheet(self):
        return self.find_ancestor(ExcelWorksheet)


########################################################################
# Excel Application Delegation
########################################################################

class ExcelApplication(ComObject):

    @staticmethod
    def start(visible=True):
        logging.debug("Start Excel process")

        com = ApplicationClass()
        com.Visible = MsoTriState.msoTrue if visible else MsoTriState.msoFalse
        com.DisplayAlerts = False

        atexit_register(com.Quit, "End Excel process")
        return com


    @staticmethod
    def find():
        logging.debug("Find Excel process")

        try:
            return Marshal.GetActiveObject("Excel.Application")
        except (COMException, IOError):
            return None


    def __init__(self, visible=True):
        super(ExcelApplication, self).__init__(
            self.__class__.find() or self.__class__.start(visible),
            None)
        self._workbooks = ExcelWorkbooks(self._com.Workbooks, self)

    def __del__(self):
        if self._workbooks != None:
            del self._workbooks
            self._workbooks = None        
        super(ExcelApplication, self).__del__()


    @property
    def Workbooks(self):
        return self._workbooks
    
    @property
    def DisplayAlerts(self):
        return self._com.DisplayAlerts
    
    @DisplayAlerts.setter
    def DisplayAlerts(self, value):
        self._com.DisplayAlerts = value

    @property
    def Visible(self):
        return self._com.Visible
    
    @Visible.setter
    def Visible(self, value):
        self._com.Visible = value
    

    

########################################################################
# Excel Workbooks Delegation
########################################################################

class ExcelWorkbooks(ComObject):

    def __init__(self, com, parent):
        super(ExcelWorkbooks, self).__init__(com, parent)
        self._wblist = []
        

    def __del__(self):
        for wb in self._wblist:
            del wb
            self._wblist = []
        super(ExcelWorkbooks, self).__del__()

    @property
    def Count(self):
        return self._com.Count
    
            
    def find(self, path):
        logging.debug("{0} find {1}".format(self.__class__.__name__, path))

        fullname = FullName(path)

        try:
            return next(wb for wb in self._wblist if wb.FullName == fullname)
        except StopIteration:
            pass
        
        try:
            wb = ExcelWorkbook(next(
                wbcom for wbcom in self._com
                if wbcom.FullName == fullname), self)
            self._wblist.append(wb)
            
            return wb
        except StopIteration:
            return None

        return None
    

    def open(self, path):
        logging.debug("{0} open {1}".format(self.__class__.__name__, path))
        
        fullname = FullName(path)        
        try:
            wbcom = self._com.Open(fullname)
        except COMException:
            return None

        if wbcom != None:
            wb = ExcelWorkbook(wbcom, self)
            self._wblist.append(wb)
            return wb
        else:
            return None


    def create(self, path):
        logging.debug("{0} create {1}".format(self.__class__.__name__, path))

        fullname = FullName(path)        
        wbcom = self._com.Add(Missing.Value)
        if wbcom != None:
            wb = ExcelWorkbook(wbcom, self)
            try:
                wb.SaveAs(fullname)
                self._wblist.append(wb)
            except System.Runtime.InteropServices.COMException:
                logging.error("Failed to save as {0}", path)
            return wb

        logging.error("{0} failed to create {1}".format(
            self.__class__.__name__, path))
        return None

    def __call__(self, path):
        return self.find(path) or self.open(path) or self.create(path)

    

########################################################################
# Excel Workbook Delegation
########################################################################

class ExcelWorkbook(ComObject):

    def __init__(self, com, parent):
        super(ExcelWorkbook, self).__init__(com, parent)

        # TODO: Needs to be saved ?
        if self.Saved is not True:
            self.Save()
        self._worksheets = ExcelWorksheets(self._com.Worksheets, self)
        

    def __del__(self):
        if self._worksheets != None:
            del self._worksheets
            self._worksheets = None
        super(ExcelWorkbook, self).__del__()

        
    @property
    def Worksheets(self):
        return self._worksheets

    @property
    def FullName(self):
        return self._com.FullName
    
    @property
    def Path(self):
        return self._com.Path
    
    @property
    def Saved(self):
        return self._com.Saved
    
    def Save(self):
        self._com.Save()
        
    def SaveAs(self, path):
        self._com.SaveAs(
            FullName(path),
            ExcelFileFormat(path),
            Missing.Value,
            Missing.Value,
            Missing.Value,
            Missing.Value,
            XlSaveAsAccessMode.xlExclusive,
            Missing.Value,
            Missing.Value,
            Missing.Value,
            Missing.Value,
            Missing.Value
        )

    def Close(self, _SaveChanges=True):
        self._com.Close(_SaveChanges)
    

########################################################################
# Excel Worksheets Delegation
########################################################################

class ExcelWorksheets(ComObject):

    def __init__(self, com, parent):
        super(ExcelWorksheets, self).__init__(com, parent)
        self._wslist = []
        

    def __del__(self):
        for key, sheet in self._wslist:
            del sheet
            self._wslist = []
        super(ExcelWorksheets, self).__del__()

            
    def find(self, name):
        logging.debug("Find {0} worksheet".format(name))

        try:
            return next(ws for ws in self._wslist if ws.Name == name)
        except StopIteration:
            return None


    def open(self, name):
        logging.debug("Open {0} worksheet".format(name))

        try:
            ws = ExcelWorksheet(next(
                wscom for wscom in self._com if wscom.Name == name), self)
            self._wslist.append(ws)
            return ws
        except StopIteration:
            return None

        
    def create(self, name):
        logging.debug("Create {0} worksheet".format(name))

        ws = ExcelWorksheet(self._com.Add(), self)
        ws.Name = name
        self._wslist.append(ws)
        return ws

    
    def __call__(self, name):
        return self.find(name) or self.open(name) or self.create(name)

    @property
    def Count(self):
        return self._com.Count

    
########################################################################
# Excel RangeBase Delegation
########################################################################

class ExcelRangeBase(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelRangeBase, self).__init__(com, parent)

        self._cells = ExcelCells(self._com.Cells, self)
        self._rows = ExcelRange(self._com.Rows, self)
        self._columns = ExcelRange(self._com.Columns, self)
        

    def __del__(self):
        if self._columns != None:
            del self._columns
            self._columns = None
            
        if self._rows != None:
            del self._rows
            self._rows = None
            
        if self._cells != None:
            del self._cells
            self._cells = None

        super(ExcelRangeBase, self).__del__()
            
    @property
    def Columns(self):
        return self._columns

    @property
    def Rows(self):
        return self._rows

    @property
    def Cells(self):
        return self._cells


########################################################################
# Excel Range Delegation
########################################################################

class ExcelRange(ComObject):

    def __init__(self, com, parent):
        super(ExcelRange, self).__init__(com, parent)
        
    def __del__(self):
        super(ExcelRange, self).__del__()

    @property
    def Row(self):
        return self._com.Row

    @property
    def Column(self):
        return self._com.Column
    
    @property
    def Rows(self):
        return ExcelRange(self._com.Rows, self)

    @property
    def Columns(self):
        return ExcelRange(self._com.Columns, self)
    
    @property
    def Top(self):
        return self._com.Top

    @property
    def Left(self):
        return self._com.Left

    @property
    def Height(self):
        return self._com.Height

    @property
    def Width(self):
        return self._com.Width

    @property
    def RowHeight(self):
        return self._com.RowHeight

    @RowHeight.setter
    def RowHeight(self, value):
        self._com.RowHeight = value

    @property
    def ColumnWidth(self):
        return self._com.ColumnWidth

    @ColumnWidth.setter
    def ColumnWidth(self, value):
        self._com.ColumnWidth = value

    @property
    def Count(self):
        return self._com.Count

    @property
    def Value(self):
        return self._com.Value

    @property
    def MergeCells(self):
        return self._com.MergeCells

    # For convenience
    @property
    def value(self):
        return self.Value[XlRangeValueDataType.xlRangeValueDefault]

    @value.setter
    def value(self, value):
        self.Value[XlRangeValueDataType.xlRangeValueDefault] = value

    @property
    def text(self):
        return str(self.value or "")

    @text.setter
    def text(self, value):
        self.value = value



########################################################################
# Excel Worksheet Delegation
########################################################################

class ExcelWorksheet(ComObject):

    def __init__(self, com, parent):
        super(ExcelWorksheet, self).__init__(com, parent)
        self._rngdic = {}

    def __del__(self):
        for key, rng in self._rngdic.iteritems():
            del rng
        self._rngdic = None
        super(ExcelWorksheet, self).__del__()

    def _add_range(self, rngcom):
        key = (rngcom.Row, rngcom.Column,
            rngcom.Rows.Count, rngcom.Columns.Count)
        self._rngdic[key] = ExcelRange(rngcom, self)
        return self._rngdic[key]
            
    def Range(self, cell_tl, cell_br):
        key = (
                cell_tl.Row,
                cell_tl.Column,
                cell_br.Row - cell_tl.Row + 1,
                cell_br.Column - cell_tl.Column + 1
                )
        if self._rngdic.has_key(key):
            return self._rngdic[key]
        else:
            return self._add_range(
                    self._com.Range(cell_tl._com, cell_br._com))

    def Cells(self, row, column):
        return self._add_range(ExcelRange(self._com.Cells(row, column), self))
        
    @property
    def UsedRange(self):
        return self._add_range(self._com.UsedRange)
        
    @property
    def Name(self):
        return self._com.Name
    
    @Name.setter
    def Name(self, name):
        self._com.Name = name
        
    @property
    def Index(self):
        return self._com.Index

    @property
    def StandardHeight(self):
        return self._com.StandardHeight
        
    @property
    def StandardWidth(self):
        return self._com.StandardWidth

    
########################################################################
# Excel Columns Delegation
########################################################################

class ExcelListColumns(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelListColumns, self).__init__(com, parent)
        self._coldic = {}
        

    def __del__(self):
        for num, col in self._coldic.iteritems():
            del col
        self._coldic = {}
        super(ExcelListColumns, self).__del__()

    @property            
    def Count(self):
        return self._com.Count


    def Item(self, num):
        try:
            return self._coldic[num]
        except KeyError:
            pass

        self._coldic[num] = ExcelListColumn(self._com.Item(num), self)
        return self._coldic[num]

    
########################################################################
# Excel Rows Delegation
########################################################################

class ExcelListRows(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelListRows, self).__init__(com, parent)
        self._rowdic = {}
        

    def __del__(self):
        for num, row in self._rowdic.iteritems():
            del row
        self._rowdic = {}
        super(ExcelListRows, self).__del__()

    @property            
    def Count(self):
        return self._com.Count


    def Item(self, num):
        try:
            return self._rowdic[num]
        except KeyError:
            pass

        self._rowdic[num] = ExcelListRow(self._com.Item(num), self)
        return self._rowdic[num]

    
########################################################################
# Excel Cells Delegation
########################################################################

class ExcelCells(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelCells, self).__init__(com, parent)
        self._celldic = {}
        

    def __del__(self):
        for num, cell in self._celldic.iteritems():
            del cell
        self._celldic = {}
        super(ExcelCells, self).__del__()

    def __call__(self, row, col):
        key = (row, col)
        if self._celldic.has_key(key):
            return self._celldic[(row, col)]
        else:
            self._celldic[(row, col)] = ExcelRange(self._com(row, col), self)
            return self._celldic[(row, col)]

    
########################################################################
# Excel Column Delegation
########################################################################

class ExcelListColumn(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelListColumn, self).__init__(com, parent)
        

    def __del__(self):
        super(ExcelListColumn, self).__del__()

    @property            
    def Index(self):
        return self._com.Index
    
        
    
########################################################################
# Excel Row Delegation
########################################################################

class ExcelListRow(WorksheetComObject):

    def __init__(self, com, parent):
        super(ExcelListRow, self).__init__(com, parent)

    def __del__(self):
        super(ExcelListRow, self).__del__()
            
    @property            
    def Index(self):
        return self._com.Index
    
           
########################################################################
# Main
########################################################################

if __name__ == '__main__':
    import unittest
    from test.excel_test import *
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main(verbosity=2)

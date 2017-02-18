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
import traceback

from itertools import chain
from itertools import ifilter
from itertools import imap
from itertools import izip

from singleton import *

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
                logging.info("{0}".format(text))
            traceback.print_exc()
    return atexit.register(lambda: _(func))


########################################################################
# Excel Cell Name
########################################################################

def digiseq(val, base):
    return ((val % base),) if val < base else \
            digiseq(val // base, base) + digiseq(val % base, base)


def colname(val):
    def _add1(seq):
        return seq[0:-1] + (seq[-1] + 1,)
    return ''.join(map(lambda d: chr(ord('A') + d - 1),
            _add1(digiseq(val - 1, 26))))


def colval(name):
    return reduce(lambda val, ch: val*26 + ord(ch) - ord('A') + 1,
            name.upper(), 0)


def cellname(row, col):
    return colname(col) + str(row)


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
            Marshal.FinalReleaseComObject(self._com)
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

    __metaclass__ = Singleton

    @staticmethod
    def start(visible=True):
        logging.debug("Start Excel process")

        com = ApplicationClass()
        com.Visible = MsoTriState.msoTrue if visible else MsoTriState.msoFalse
        com.DisplayAlerts = False

        #atexit_register(com.Quit, "End Excel process")
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

    __metaclass__ = Singleton

    def __init__(self, com, parent):
        super(ExcelWorkbooks, self).__init__(com, parent)
        self._wbdic = {}
        

    def __del__(self):
        for wb in self._wbdic.values():
            del wb
            self._wbdic = {}
        super(ExcelWorkbooks, self).__del__()

    @property
    def Count(self):
        return self._com.Count
    
    def find(self, path):
        logging.debug("{0} find {1}".format(self.__class__.__name__, path))

        return self._wbdic[path] if path in self._wbdic else None
    
    def open(self, path):
        logging.debug("{0} open {1}".format(self.__class__.__name__, path))
        
        try:
            wbcom = self._com.Open(path)
        except COMException:
            return None

        if wbcom != None:
            wb = ExcelWorkbook(wbcom, self)
            self._wbdic[path] = wb
            return wb
        else:
            return None

    def create(self, path):
        logging.debug("{0} create {1}".format(self.__class__.__name__, path))
        wbcom = self._com.Add(Missing.Value)
        if wbcom != None:
            wb = ExcelWorkbook(wbcom, self)
            try:
                wb.SaveAs(path)
                self._wbdic[path] = wb
            except System.Runtime.InteropServices.COMException:
                logging.error("Failed to save as {0}", path)
            return wb

        logging.error("{0} failed to create {1}".format(
            self.__class__.__name__, path))
        return None

    def __call__(self, path):
        fullname = FullName(path)        
        return self.find(fullname) or \
                self.open(fullname) or \
                self.create(fullname)

    

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
# Excel Worksheet Delegation
########################################################################

class ExcelWorksheet(ComObject):

    def __init__(self, com, parent):
        super(ExcelWorksheet, self).__init__(com, parent)
        self._rangedic = {}

    def __del__(self):
        for key, rng in self._rangedic.iteritems():
            del rng
        self._rangedic = None

        super(ExcelWorksheet, self).__del__()

    def _add_range(self, rngcom):
        key = (rngcom.Row, rngcom.Column,
            rngcom.Rows.Count, rngcom.Columns.Count)
        if rngcom.Rows.Count == 1 and rngcom.Columns.Count == 1:
            self._rangedic[key] = ExcelCell(rngcom, self)
        else:
            self._rangedic[key] = ExcelRange(rngcom, self)
        return self._rangedic[key]
            
    def Range(self, cell_tl, cell_br):
        key = (
                cell_tl.Row,
                cell_tl.Column,
                cell_br.Row - cell_tl.Row + 1,
                cell_br.Column - cell_tl.Column + 1
                )
        if self._rangedic.has_key(key):
            return self._rangedic[key]
        else:
            return self._add_range(
                    self._com.Range(cell_tl._com, cell_br._com))

    def Cells(self, row, column):
        return self._add_range(
                ExcelCell(self._com.Range(cellname(row, column)), self))
        
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
# Excel Range Delegation
########################################################################

class ExcelRange(ComObject):

    def __init__(self, com, worksheet):
        super(ExcelRange, self).__init__(com, worksheet)
        
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


class ExcelCell(ExcelRange):

    def __init__(self, com, worksheet):
        super(ExcelCell, self).__init__(com, worksheet)
        
    def __del__(self):
        super(ExcelCell, self).__del__()

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
# Excel Rows
########################################################################

class ExcelRows(ExcelRange):

    def __init__(self, com, worksheet):
        super(ExcelRows, self).__init__(com, worksheet)
        
    def __del__(self):
        super(ExcelRows, self).__del__()

    @property            
    def Count(self):
        return self._com.Count

    def Item(self, num):
        return ExcelRange(self._com.Item(num), self._parent)

    
########################################################################
# Excel Columns
########################################################################

class ExcelColumns(ExcelRange):

    def __init__(self, com, worksheet):
        super(ExcelColumns, self).__init__(com, worksheet)
        
    def __del__(self):
        super(ExcelColumns, self).__del__()

    @property            
    def Count(self):
        return self._com.Count

    def Item(self, num):
        return ExcelRange(self._com.Item(num), self._parent)

    
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

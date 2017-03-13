#!/usr/bin/env ipy.exe
# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8:
#

import clr
clr.AddReference('office')
clr.AddReference('Microsoft.Office.Interop.Excel')

import System

from Microsoft.Office.Core import MsoTriState
from Microsoft.Office.Interop.Excel import ApplicationClass \
        as ExcelApplicationClass

from System.Runtime.InteropServices import Marshal
from System.Runtime.InteropServices import COMException


class ComProxy(object):

    __slots__ = ["_com", "__weakref__"]

    @staticmethod
    def com(inst):
        return object.__getattribute__(inst, "_com")

    def __init__(self, com):
        object.__setattr__(self, "_com", com)

    def __del__(self):
        if self._com != None:
            Marshal.ReleaseComObject(self._com)
            # Marshal.FinalReleaseComObject(self._com)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_com"), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_com"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_com"), name, value)

    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_com"))

    def __str__(self):
        return str(object.__getattribute__(self, "_com"))

    def __repr__(self):
        return repr(object.__getattribute__(self, "_com"))


def start_excel(visible=True):
    #com = ApplicationClass()
    com = ExcelApplicationClass()
    com.Visible = MsoTriState.msoTrue if visible else MsoTriState.msoFalse
    com.DisplayAlerts = False

    return com


def find_excel():
    try:
        return Marshal.GetActiveObject("Excel.Application")
    except (COMException, IOError):
        return None


########################################################################
# Main
########################################################################

if __name__ == '__main__':
    import unittest
    import logging
    from test.comproxy_test import *
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main(verbosity=2)

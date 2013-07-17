"""This module ..."""
from __future__ import print_function, division

import os
import abc
import wx

import wx.lib.dialogs as wxdg 
import abipy.gui.awx as awx
import abipy.gui.electronswx as ewx

from collections import OrderedDict

from abipy import abifile_subclass_from_filename, abiopen
from abipy.iotools.files import NcDumper, AbinitNcFile, AbinitTextFile, get_filestat
from abipy import WFK_File, SIGRES_File
from abipy.electrons.bse import MDF_Reader, MDF_File
from .abievents import AbinitEventsFrame


__all__ = [
    "popupmenu_for_filename",
]


def popupmenu_for_filename(parent, filename):
    """
    Factory function that returns the appropriate popup menu. 

    Args:
        parent:
            The parent wx window. Used to connect the children created
            by the popupmenu to the calling window.
    """

    if filename.endswith(".nc"):
        menu = NcFilePopupMenu.from_filename(filename)
    else:
        # abinit main output file or log file.
        menu = AbinitTextFilePopupMenu()

    menu.set_target(filename)
    menu.set_parent(parent)
    return menu

#--------------------------------------------------------------------------------------------------
# Callbacks

def showNcdumpMessage(parent, filepath):
    """Open a dialog with the output of ncdump."""
    caption = "ncdump output for file %s" % filepath
    msg = NcDumper().dump(filepath)
    style = wx.DEFAULT_FRAME_STYLE
    wxdg.ScrolledMessageDialog(parent, msg, caption=caption, size=(600, 600), style=style).Show()


def showFileStat(parent, filepath):
    """Open a dialog reporting file stats."""
    caption = "Info on file %s" % filepath
    stat_dict = get_filestat(filepath)
    msg = str(stat_dict)
    style = wx.DEFAULT_FRAME_STYLE
    wxdg.ScrolledMessageDialog(parent, msg, caption=caption, size=(600, 600), style=style).Show()


def showAbinitEvents(parent, filepath):
    """Open a dialog reporting file stats."""
    frame = AbinitEventsFrame(parent, filepath)
    frame.Show()

def showStructure(parent, filepath):
    ncfile = abiopen(filepath)
    structure = ncfile.get_structure() 
    visu = structure.visualize("xcrysden")
    visu()

#--------------------------------------------------------------------------------------------------

class PopupMenu(wx.Menu):
    """
    Base class for popup menus. `A PopupMenu` has a list of callback functions
    indexed by the menu title. The signature of the callback function is func(filename, parent) where 
    filename is the name of the file selected in the Widget and parent is the wx
    Window that will become the parent of the new frame created by the callback.
    """
    MENU_TITLES = {}
    #MENU_TITLES = OrderedDict([
    #    ("properties", showFileStat),
    #])
    HANDLED_FILES = []

    def __init__(self):
        super(PopupMenu, self).__init__()
        self._make_menu()

    @staticmethod
    def from_filename(filename):
        """
        Static factory function that instanciates the appropriate subclass of `NcFilePopupMenu`
        """
        # Find the AbinitNcFile subclass associated to files.
        file_class = abifile_subclass_from_filename(filename)

        # Check whether a subclass handles this file..
        # Fallback to a simple PopupMenu if no match.
        for popsubc in PopupMenu.__subclasses__():
            if popsubc.handle_file_class(file_class):
                return popsubc()
        else:
            return PopupMenu()

    @classmethod
    def handle_file_class(cls, file_class):
        """True if the popupmenu is associated to file_class."""
        return file_class in cls.HANDLED_FILES

    def _make_menu(self):
        """Build the menu taking into account the options of the superclasses."""
        base_classes = list(self.__class__.__bases__) + [self.__class__]
        base_classes.reverse()

        assert not hasattr(self, "menu_title_by_id")
        assert not hasattr(self, "menu_titles")
        self.menu_title_by_id, self.menu_titles = OrderedDict(), OrderedDict()

        for cls in base_classes:
            try:
                menus = cls.MENU_TITLES
            except AttributeError as exc:
                awx.WARNING("exc ",exc," for cls", cls)
                continue

            self.menu_titles.update(menus)

            for title in menus:
                self.menu_title_by_id[wx.NewId()] = title

            # Add sentinel for Menu separator.
            self.menu_title_by_id["separator_" + str(len(self.menu_titles))] = None
                                                                  
        for (id, title) in self.menu_title_by_id.items():
            if title is None:
                sepid = int(id.split("_")[-1])
                if sepid != len(self.menu_titles):
                    self.AppendSeparator()
            else:
                # Register menu handlers with EVT_MENU, on the menu.
                self.Append(id, title)
                wx.EVT_MENU(self, id, self.OnMenuSelection)

    def set_parent(self, parent):
        """Set the parent window."""
        self._parent = parent

    @property
    def parent(self):
        """Returns the parent window."""
        try:
            return self._parent
        except AttributeError:
            awx.WARNING("Popup menu doesn't haveparent")
            return None

    def set_target(self, target):
        """Set the target of the callback."""
        self._target = target

    @property
    def target(self):
        """The target of the callback."""
        try:
            return self._target
        except AttributeError:
            return None

    def _get_callback(self, title):
        return self.menu_titles[title]

    def OnMenuSelection(self, event):
        title = self.menu_title_by_id[event.GetId()]
        callback = self._get_callback(title)
        #print("Calling callback %s on target %s" % (callback, self.target))
        try:
            callback(parent=self.parent, filepath=self.target)
        except:
            awx.showErrorMessage(parent=self.parent)


class AbinitTextFilePopupMenu(PopupMenu):
    """
    """
    MENU_TITLES = OrderedDict([
        ("events",     showAbinitEvents),
    ])

    HANDLED_FILES = [AbinitTextFile]


class NcFilePopupMenu(PopupMenu):
    """
    Base class for popup menus. `A PopupMenu` has a list of callback functions
    indexed by the menu title and a list of `AbinitNcFile` associated to it.
    The signature of the callback function is func(filename, parent) where 
    filename is the name of the file selected in the Widget and parent is the wx
    Window that will become the parent of the new frame created by the callback.

    How to subclass PopupMenu:

        1. Define a new class that inherits from NcFilePopupMenu. 

        2. Define the callbacks in the class variable MENU_TITLES.
           Use OrderedDict to have a fixed ordering of the labels.

        3. Define the class variable HANDLED_FILES with the list of 
           `AbinitNcFile` subclasses associated to the popupmenu.

        4. Done (most of the work is indeed done in the base class and in 
           the factory function popupmenu_for_filename.
    """
    MENU_TITLES = OrderedDict([
        ("properties", showFileStat),
        ("structure",  showStructure),
        ("ncdump",     showNcdumpMessage),
    ])

    HANDLED_FILES = []


class EbandsPopupMenu(NcFilePopupMenu):
    """Popup menu for Netcdf files that contain the electron band structure."""
    MENU_TITLES = OrderedDict([
        ("ePlot", ewx.showElectronBandsPlot),
        ("eDos",  ewx.showElectronDosFrame),
    ])

    HANDLED_FILES = [WFK_File] 


def showQPData(parent, filepath):
    sigres = abiopen(filepath)
    qps_spin = sigres.get_allqps()
    assert len(qps_spin) == 1
    qps_spin[0].plot_qps_vs_e0()


class SigResPopupMenu(NcFilePopupMenu):
    """Popup menu for SIGRES files."""
    MENU_TITLES = OrderedDict([
        ("qpDataPlot", showQPData),
    ])

    HANDLED_FILES = [SIGRES_File] 


def showEXCMDF(parent, filepath):
    mdf_file = MDF_File(filepath)
    mdf_file.plot_mdfs()


class MDFPopupMenu(NcFilePopupMenu):
    """Popup menu for MDF files."""
    MENU_TITLES = OrderedDict([
        ("mdfPlot", showEXCMDF),
    ])

    HANDLED_FILES = [MDF_File] 


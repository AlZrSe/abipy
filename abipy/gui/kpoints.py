from __future__ import print_function, division

import wx

import abipy.gui.awx as awx
import wx.lib.mixins.listctrl as listmix

from collections import OrderedDict


class KpointsListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    """
    ListCtrl containing k-points. Support column sorting.
    """
    def __init__(self, parent, kpoints, **kwargs):
        """
        Args:
            parent:
                Parent window.
            kpoints:
                List of `Kpoint` instances.
        """
        super(KpointsListCtrl, self).__init__(parent, id=-1, style=wx.LC_REPORT | wx.BORDER_SUNKEN, **kwargs)

        self.kpoints = kpoints

        columns = ["#", 'Reduced coordinates', 'Weight', 'Name']

        for (index, col) in enumerate(columns):
            self.InsertColumn(index, col)

        # Used to store the Max width in pixels for the data in the column.
        column_widths = [awx.get_width_height(self, s)[0] for s in columns]

        # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
        self.itemDataMap = {}

        for (index, kpt) in enumerate(self.kpoints):
            entry = ["%d\t\t" % index, 
                     "[%.5f,  %.5f,  %.5f]\t\t" % tuple(c for c in kpt.frac_coords), 
                     "%.3f\t\t" % kpt.weight, 
                     "%s" % kpt.name,
                     ]
            self.Append(entry)
            self.itemDataMap[index] = entry
            self.SetItemData(index, index)

            w = [awx.get_width_height(self, s)[0] for s in entry]
            column_widths = map(max, zip(w, column_widths))

        for (index, col) in enumerate(columns):
            self.SetColumnWidth(index, column_widths[index])

        # Now that the list exists we can init the other base class, see wx/lib/mixins/listctrl.py
        listmix.ColumnSorterMixin.__init__(self, len(columns))

    def GetListCtrl(self):
        """Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py"""
        return self

    def getSelectedKpoint(self):
        """
        Returns the kpoint selected by the user.
        None if no selection has been done.
        """
        # Get selected index, map to index in kpoints and return the kpoint.
        item = self.GetFirstSelected()
        if item == -1: return None
        index = self.GetItemData(item)
        return self.kpoints[index]


class KpointsPanel(awx.Panel):
    """
    A panel with a list of k-points and a structure. 
    Provides popup menus for inspecting the k-points.
    """
    def __init__(self, parent, structure, kpoints, **kwargs):
        """
        Args:
            parent:
                Parent window.
            structure:
                `Structure` object.
            kpoints:
                `KpointList` object. 
        """
        super(KpointsPanel, self).__init__(parent, **kwargs)

        self.klist_ctrl = KpointsListCtrl(self, kpoints)
        self.structure = structure

        # Connect the events whose callback will be set by the client code.
        self.klist_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRightClick)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.klist_ctrl, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SetSizerAndFit(main_sizer)

    def onRightClick(self, event):
        """Generate the popup menu."""
        kpoint = self.klist_ctrl.getSelectedKpoint()

        popup_menu = self.makePopupMenu()
        self.PopupMenu(popup_menu, event.GetPoint())
        popup_menu.Destroy()

    def makePopupMenu(self):
        """
        Build and return a popup menus so that subclasses can extend 
        or replace this base method.
        """
        self.ID_POPUP_LITTLEGROUP = wx.NewId()
        self.ID_POPUP_STAR = wx.NewId()

        menu = wx.Menu()
        menu.Append(self.ID_POPUP_LITTLEGROUP, "Little group")
        menu.Append(self.ID_POPUP_STAR, "Show star")

        # Associate menu/toolbar items with their handlers.
        menu_handlers = [
            (self.ID_POPUP_LITTLEGROUP, self.onLittleGroup),
            (self.ID_POPUP_STAR, self.onShowStar),
        ]
                                                            
        for combo in menu_handlers:
            mid, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id=mid)
                                                     
        return menu

    def onLittleGroup(self, event):
        kpoint = self.klist_ctrl.getSelectedKpoint()
        ltk = self.structure.spacegroup.find_little_group(kpoint)
        table, header = ltk.bilbao_character_table()
        awx.SimpleGridFrame(self, table, title=header, labels_from_table=True).Show()

    def onShowStar(self, event):
        kpoint = self.klist_ctrl.getSelectedKpoint()
        star = kpoint.compute_star(self.structure.fm_symmops)
        KpointsFrame(self, self.structure, star, title="Star of point: " + str(star.base_point)).Show()


class KpointsFrame(awx.Frame):
    def __init__(self, parent, structure, kpoints, **kwargs):
        """
        Args:
            parent:
                Parent window.
            structure:
                `Structure` object.
            kpoints:
                `KpointList` object. 
        """
        super(KpointsFrame, self).__init__(parent, **kwargs)

        self.panel = KpointsPanel(self, structure, kpoints)

        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(self.panel, 1, wx.EXPAND, 5)
        #self.SetSizer(sizer)


class SpinKpointBandPanel(awx.Panel):
    """
    This panel shows information on the k-points and the set of bands, spins. 
    Useful if we want to allow the user to select the set of indices (spin, kpt_idx, band).
    """
    def __init__(self, parent, nsppol, kpoints, mband, bstart=0, **kwargs):
        """
        Args:
            nsppol:
                Number of spins.
            kpoints:
                List of `Kpoint` instances.
            mband:
                Maximum band index.
            bstart:
                First band index.
        """
        super(SpinKpointBandPanel, self).__init__(parent, style=wx.LC_REPORT | wx.BORDER_SUNKEN, **kwargs) 

        self.nsppol, self.kpoints, self.mband = nsppol, kpoints, mband
        self.bstart = bstart

        self.BuildUi()

    def BuildUi(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)

        band_label = wx.StaticText(self, -1, "Band:", wx.DefaultPosition, wx.DefaultSize, 0)
        band_label.Wrap(-1)
        hsizer1.Add(band_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT, 5)

        self.band_cbox = wx.ComboBox(self, -1, choices=map(str, range(self.bstart, self.mband)))
        hsizer1.Add(self.band_cbox, 0, wx.ALL, 5)

        spin_label = wx.StaticText(self, -1, "Spin:", wx.DefaultPosition, wx.DefaultSize, 0)
        spin_label.Wrap(-1)
        hsizer1.Add(spin_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT, 5)

        self.spin_cbox = wx.ComboBox(self, -1, choices=map(str, range(self.nsppol)))
        hsizer1.Add(self.spin_cbox, 0, wx.ALL, 5)

        main_sizer.Add(hsizer1, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)

        kpoint_label = wx.StaticText(self, -1, "Kpoint:", wx.DefaultPosition, wx.DefaultSize, 0)
        kpoint_label.Wrap(-1)
        hsizer2.Add(kpoint_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.klist_ctrl = klist = KpointsListCtrl(self, self.kpoints)

        hsizer2.Add(self.klist_ctrl, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        main_sizer.Add(hsizer2, 1, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SetSizerAndFit(main_sizer)

        # Connect the events whose callback will be set by the client code.
        klist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        klist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        klist.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def GetSKB(self):
        """Returns the tuple (spin, kpoint, band) selected by the user."""
        spin = int(self.spin_cbox.GetValue())
        kpoint = self.klist_ctrl.getSelectedKpoint()
        band = int(self.band_cbox.GetValue())
        return spin, kpoint, band

    def SetOnRightClick(self, callback):
        """
        Set the callback when EVT_LIST_ITEM_RIGHT_CLICK is fired.
        The callback expects the tuple (spin, kpoint, band)
        """
        self._on_item_right_click_callback = callback

    def OnRightClick(self, event):
        """Call the callback registered with `SetOnRightClick` (if any)."""
        if hasattr(self, "_on_item_right_click_callback"):
            #print("In OnRightClick with skb %s" % str(skb))
            skb = self.GetSKB()
            self._on_item_right_click_callback(*skb)

    def SetOnItemSelected(self, callback):
        """
        Set the callback when EVT_LIST_ITEM_SELECTED is fired.
        The callback expects the tuple (spin, kpoint, band)
        """
        self._on_item_selected_callback = callback

    def OnItemSelected(self, event):
        """Call the callback registered with `SetOnItemSelected` (if any)."""
        if hasattr(self, "_on_item_selected_callback"):
            #print("In OnItemSelected with skb %s" % str(skb))
            skb = self.GetSKB()
            self._on_item_selected_callback(*skb)

    def SetOnItemActivated(self, callback):
        """
        Set the callback when EVT_LIST_ITEM_ACTIVATED is fired (double click).
        The callback expects the tuple (spin, kpoint, band)
        """
        self._on_item_activated_callback = callback

    def OnItemActivated(self, event):
        """Call the callback registered with `SetOnItemActivated` (if any)."""
        if hasattr(self, "_on_item_activated_callback"):
            skb = self.GetSKB()
            #print("In OnItemActivated with skb %s" % str(skb))
            self._on_item_activated_callback(*skb)































































from __future__ import print_function, division

import sys

import wx
import wx.grid as  gridlib

__all__ = [
    "SimpleGrid",
    "SimpleGridFrame",
]

class SimpleGrid(gridlib.Grid): 

    def __init__(self, parent, table, row_labels=None, col_labels=None):
        """
        Args:
            parent:
                parent window.
            table:
                List of string lists.
            row_labels:
                List of strings used to name the rows.
            col_labels:
                List of strings used to name the col.
        """

        gridlib.Grid.__init__(self, parent, -1)
        self.log = sys.stdout

        self.moveTo = None
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
        self.nrows = nrows = len(table)
        dims = set([len(row) for row in table])
        if len(dims) == 1:
            self.ncols = ncols = list(dims)[0]
        else:
            raise ValueError("Each row must have the same number of columns but dims %s" % str(dims))

        self.CreateGrid(nrows, ncols)
        
        attr = gridlib.GridCellAttr()
        attr.SetTextColour(wx.BLACK)
        attr.SetBackgroundColour(wx.WHITE)
        attr.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.SetGridCellAttr(attr)

        if row_labels is not None:
            assert len(row_labels) == nrows
            for i, label in enumerate(row_labels):
                self.SetRowLabelValue(i, label)

        if col_labels is not None:
            assert len(col_labels) == ncols
            for i, label in enumerate(col_labels):
                self.SetColLabelValue(i, label)
            self.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_BOTTOM)

        # cell formatting
        for r, row in enumerate(table):
            for c, col in enumerate(row):
                self.SetCellValue(r, c, table[r][c])
                self.SetReadOnly(r, c, True)

        self.AutoSize()
        self.ForceRefresh()

        # test all the events
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_DCLICK, self.OnCellRightDClick)

        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.OnLabelLeftDClick)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_DCLICK, self.OnLabelRightDClick)

        self.Bind(gridlib.EVT_GRID_ROW_SIZE, self.OnRowSize)
        self.Bind(gridlib.EVT_GRID_COL_SIZE, self.OnColSize)

        self.Bind(gridlib.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.OnCellChange)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectCell)

        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self.OnEditorShown)
        self.Bind(gridlib.EVT_GRID_EDITOR_HIDDEN, self.OnEditorHidden)
        self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.OnEditorCreated)

    def SetGridCellAttr(self, attr):
        """
        Set cell attributes for the whole row.

        Args:
            attr:
                `gridlib.GridCellAttr`
        """
        # Note that GridCellAttr objects are reference counted, so attr.IncRef 
        # should be called every time Grid.Set*Attr(attr) is called. This is 
        # required to keep the Grid.Delete* methods from unexpectedly deleting the 
        # GridCellAttr object. 
        for row in range(self.nrows):
            attr.IncRef()
            self.SetRowAttr(row, attr)
        self.AutoSize()
        self.ForceRefresh()

    def OnCellLeftClick(self, evt):
        self.log.write("OnCellLeftClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnCellRightClick(self, evt):
        self.log.write("OnCellRightClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnCellLeftDClick(self, evt):
        self.log.write("OnCellLeftDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnCellRightDClick(self, evt):
        self.log.write("OnCellRightDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelLeftClick(self, evt):
        self.log.write("OnLabelLeftClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelRightClick(self, evt):
        self.log.write("OnLabelRightClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelLeftDClick(self, evt):
        self.log.write("OnLabelLeftDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelRightDClick(self, evt):
        self.log.write("OnLabelRightDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnRowSize(self, evt):
        self.log.write("OnRowSize: row %d, %s\n" % (evt.GetRowOrCol(), evt.GetPosition()))
        evt.Skip()

    def OnColSize(self, evt):
        self.log.write("OnColSize: col %d, %s\n" % (evt.GetRowOrCol(), evt.GetPosition()))
        evt.Skip()

    def OnRangeSelect(self, evt):
        if evt.Selecting():
            msg = 'Selected'
        else:
            msg = 'Deselected'
        self.log.write("OnRangeSelect: %s  top-left %s, bottom-right %s\n" %
                           (msg, evt.GetTopLeftCoords(), evt.GetBottomRightCoords()))
        evt.Skip()


    def OnCellChange(self, evt):
        self.log.write("OnCellChange: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))

        # Show how to stay in a cell that has bad data.  We can't just
        # call SetGridCursor here since we are nested inside one so it
        # won't have any effect.  Instead, set coordinates to move to in
        # idle time.
        value = self.GetCellValue(evt.GetRow(), evt.GetCol())

        if value == 'no good':
            self.moveTo = evt.GetRow(), evt.GetCol()

    def OnIdle(self, evt):
        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None

        evt.Skip()

    def OnSelectCell(self, evt):
        if evt.Selecting():
            msg = 'Selected'
        else:
            msg = 'Deselected'
        self.log.write("OnSelectCell: %s (%d,%d) %s\n" % (msg, evt.GetRow(), evt.GetCol(), evt.GetPosition()))

        # Another way to stay in a cell that has a bad value...
        row = self.GetGridCursorRow()
        col = self.GetGridCursorCol()

        if self.IsCellEditControlEnabled():
            self.HideCellEditControl()
            self.DisableCellEditControl()

        value = self.GetCellValue(row, col)

        if value == 'no good 2':
            return  # cancels the cell selection

        evt.Skip()

    def OnEditorShown(self, evt):
        if evt.GetRow() == 6 and evt.GetCol() == 3 and \
           wx.MessageBox("Are you sure you wish to edit this cell?",
                        "Checking", wx.YES_NO) == wx.NO:
            evt.Veto()
            return

        self.log.write("OnEditorShown: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnEditorHidden(self, evt):
        if evt.GetRow() == 6 and evt.GetCol() == 3 and \
           wx.MessageBox("Are you sure you wish to  finish editing this cell?",
                        "Checking", wx.YES_NO) == wx.NO:
            evt.Veto()
            return

        self.log.write("OnEditorHidden: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnEditorCreated(self, evt):
        self.log.write("OnEditorCreated: (%d, %d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetControl()))

    #def InstallGridHint(grid, rowcolhintcallback):
    #    prev_rowcol = [None,None]
    #    def OnMouseMotion(evt):
    #        # evt.GetRow() and evt.GetCol() would be nice to have here,
    #        # but as this is a mouse event, not a grid event, they are not
    #        # available and we need to compute them by hand.
    #        x, y = grid.CalcUnscrolledPosition(evt.GetPosition())
    #        row = grid.YToRow(y)
    #        col = grid.XToCol(x)
    #        if (row,col) != prev_rowcol and row >= 0 and col >= 0:
    #            prev_rowcol[:] = [row,col]
    #            hinttext = rowcolhintcallback(row, col)
    #            if hinttext is None:
    #                hinttext = ''
    #            grid.GetGridWindow().SetToolTipString(hinttext)
    #        evt.Skip()
    #    wx.EVT_MOTION(grid.GetGridWindow(), OnMouseMotion)


class SimpleGridFrame(wx.Frame):
    def __init__(self, parent, table, row_labels=None, col_labels=None, **kwargs):
        super(SimpleGridFrame, self).__init__(parent, -1, **kwargs)

        self.font_picker = wx.FontPickerCtrl(self, -1)

        self.grid = SimpleGrid(self, table, row_labels=row_labels, col_labels=col_labels)
        self.Bind(wx.EVT_FONTPICKER_CHANGED, self.OnFontPickerChanged)

        self.main_sizer = main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.font_picker)
        main_sizer.Add(self.grid)

        self.SetSizerAndFit(main_sizer)

    def OnFontPickerChanged(self, event):
        """Change the Font."""
        font = self.font_picker.GetSelectedFont()
        attr = gridlib.GridCellAttr()
        attr.SetFont(font)
        self.grid.SetGridCellAttr(attr)
        self.main_sizer.Fit(self)

#---------------------------------------------------------------------------

class TestFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Simple Grid Demo")

        row_labels = ["row1", "row2"]
        col_labels = ["col1", "col2", "col3"]

        table = [ 
            ["1", "2", "3"],
            ["4", "5", "6"]
        ]
        self.grid = SimpleGrid(self, table, row_labels, col_labels)


if __name__ == '__main__':
    app = wx.App()
    frame = TestFrame(None)
    frame.Show(True)
    app.MainLoop()

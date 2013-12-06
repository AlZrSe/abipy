from __future__ import print_function, division

import os
import wx

import wx.lib.agw.flatnotebook as fnb
import abipy.gui.awx as awx

from wx.py.shell import Shell
from abipy.abilab import abiopen
from abipy.tools import marquee, list_strings 
from abipy.electrons.bse import MDF_Plotter
from abipy.iotools.visualizer import Visualizer
from abipy.gui import mixins as mix 
from abipy.gui.kpoints import KpointsPanel


class MdfViewerFrame(awx.Frame, mix.Has_Structure, mix.Has_MultipleEbands, mix.Has_Tools, mix.Has_NetcdfFiles):
    VERSION = "0.1"

    def __init__(self, parent, filepaths=(), **kwargs):
        """
        Args:
            parent:
                parent window.
            filepaths:
                String or list of strings with the path of the netcdf MDF files to open
                Empty tuple if no file should be opened during the initialization of the frame.
        """
        super(MdfViewerFrame, self).__init__(parent, -1, title=self.codename, **kwargs)

        # This combination of options for config seems to work on my Mac.
        self.config = wx.FileConfig(appName=self.codename, localFilename=self.codename + ".ini", 
                                    style=wx.CONFIG_USE_LOCAL_FILE)

        # Build menu, toolbar and status bar.
        self.makeMenu()
        self.makeToolBar()
        self.statusbar = self.CreateStatusBar()

        # Open netcdf files.
        filepaths, exceptions = list_strings(filepaths), []
        filepaths = map(os.path.abspath, filepaths)

        # Create the notebook (each file will have its own tab).
        panel = wx.Panel(self, -1)
        self.notebook = fnb.FlatNotebook(panel, -1, style=fnb.FNB_NAV_BUTTONS_WHEN_NEEDED)
                                                                                           
        for path in filepaths:
            self.read_file(path)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND, 5)
        panel.SetSizerAndFit(sizer)

    @property
    def codename(self):
        return "MdfViewer"

    @property
    def active_tab(self):
        """Returns the active tab. None if notebook is empty."""
        return self.notebook.GetCurrentPage()

    @property
    def active_mdf_file(self):
        """The active MDF file i.e. the MDF associated to the active tab."""
        return self.active_tab.mdf_file

    @property
    def structure(self):
        """`Structure` associated to the active tab."""
        return self.active_mdf_file.structure

    @property
    def ebands(self):
        """`ElectronBands` associated to the active tab."""
        return self.active_mdf_file.ebands

    @property
    def ebands_list(self):
        """List of `ElectronBands`."""
        ebands_list = []
        for page in range(self.notebook.GetPageCount()):
            tab = self.notebook.GetPage(page)
            ebands_list.append(tab.mdf_file.ebands)
        return ebands_list

    @property
    def ebands_filepaths(self):
        """
        Return a list with the absolute paths of the files 
        from which the `ElectronBands` have been read.
        """
        paths = []
        for page in range(self.notebook.GetPageCount()):
            tab = self.notebook.GetPage(page)
            paths.append(tab.mdf_file.filepath)
        return paths

    @property
    def nc_filepaths(self):
        """String with the absolute paths of the netcdf files."""
        paths = []
        for page in range(self.notebook.GetPageCount()):
            tab = self.notebook.GetPage(page)
            paths.append(tab.mdf_file.filepath)
        return paths

    @property
    def mdf_filepaths(self):
        """
        Return a list with the absolute paths of the files 
        from which the `MDF_Files` have been read.
        """
        paths = []
        for page in range(self.notebook.GetPageCount()):
            tab = self.notebook.GetPage(page)
            paths.append(tab.mdf_file.filepath)
        return paths

    @property
    def mdf_files_list(self):
        """List of `MDF_Files`."""
        mdf_lists = []
        for page in range(self.notebook.GetPageCount()):
            tab = self.notebook.GetPage(page)
            mdf_lists.append(tab.mdf_file)
        return mdf_lists

    def makeMenu(self):
        """Creates the main menu."""
        self.menu_bar = menuBar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "&Open", help="Open an existing MDF file")
        file_menu.Append(wx.ID_CLOSE, "&Close", help="Close the MDF file")
        file_menu.Append(wx.ID_EXIT, "&Quit", help="Exit the application")

        file_history = self.file_history = wx.FileHistory(8)
        file_history.Load(self.config)
        recent = wx.Menu()
        file_history.UseMenu(recent)
        file_history.AddFilesToMenu()
        file_menu.AppendMenu(wx.ID_ANY, "&Recent Files", recent)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        menuBar.Append(file_menu, "File")

        menuBar.Append(self.CreateStructureMenu(), "Structure")
        menuBar.Append(self.CreateEbandsMenu(), "Ebands")
        menuBar.Append(self.CreateMdfMenu(), "Mdf")
        menuBar.Append(self.CreateToolsMenu(), "Tools")
        menuBar.Append(self.CreateNetcdfMenu(), "Netcdf")

        self.help_menu = wx.Menu()
        self.help_menu.Append(wx.ID_ABOUT, "About " + self.codename, help="Info on the application")
        menuBar.Append(self.help_menu, "Help")

        self.SetMenuBar(menuBar)

    def CreateMdfMenu(self):
        # MDF Menu ID's
        self.ID_MDF_PLOT = wx.NewId()
        self.ID_MDF_COMPARE = wx.NewId()
                                                                                      
        menu = wx.Menu()
        menu.Append(self.ID_MDF_PLOT, "Plot MDF", "Plot the macroscopic dielectric function")
        self.Bind(wx.EVT_MENU, self.OnMdfPlot, id=self.ID_MDF_PLOT)

        menu.AppendSeparator()

        menu.Append(self.ID_MDF_COMPARE, "Compare MDF", "Compare multiple macroscopic dielectric functions")
        self.Bind(wx.EVT_MENU, self.OnMdfCompare, id=self.ID_MDF_COMPARE)                                                                                                            

        return menu

    def OnMdfPlot(self,event):
        mdf_file = self.active_mdf_file
        mdf_file.plot_mdfs()

    def OnMdfCompare(self,event):
        plotter = MDF_Plotter()

        for path, mdf_file in zip(self.mdf_filepaths, self.mdf_files_list):
            label = os.path.relpath(path)
            # TODO
            #plotter.add_mdf(label, mdf)
            plotter.add_mdf_from_file(mdf_file.filepath)

        plotter.plot()

    def makeToolBar(self):
        """Creates the toolbar."""
        self.toolbar = toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize(wx.Size(48, 48))

        def bitmap(path):
            return wx.Bitmap(awx.path_img(path))

        artBmp = wx.ArtProvider.GetBitmap
        toolbar.AddSimpleTool(wx.ID_OPEN, artBmp(wx.ART_FILE_OPEN, wx.ART_TOOLBAR), "Open")
        toolbar.AddSeparator()

        toolbar.Realize()

        # Associate menu/toolbar items with their handlers.
        menu_handlers = [
            (wx.ID_OPEN, self.OnOpen),
            #(wx.ID_CLOSE, self.OnClose),
            #(wx.ID_EXIT, self.OnExit),
            (wx.ID_ABOUT, self.OnAboutBox),
        ]
                                                            
        for combo in menu_handlers:
            mid, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id=mid)

    def AddFileToHistory(self, filepath):
        """Add the absolute filepath to the file history."""
        self.file_history.AddFileToHistory(filepath)
        self.file_history.Save(self.config)
        self.config.Flush()

    def read_file(self, filepath):
        """Open netcdf file, create new tab and save the file in the history."""
        self.statusbar.PushStatusText("Reading %s" % filepath)
        try:
            notebook = self.notebook
            mdf_file = abiopen(filepath)
            #if not isinstance(mdf, MDF_File):
            #    awx.showErrorMessage(self, message="%s is not a valid MDF File" % filepath)
            #    return
            self.statusbar.PushStatusText("MDF file %s loaded" % filepath)
            tab = MdfFileTab(notebook, mdf_file)
            notebook.AddPage(tab, os.path.basename(filepath))
            # don't know why but this does not work!
            notebook.Refresh()
            notebook.SetSelection(notebook.GetPageCount())
            self.AddFileToHistory(filepath)
        except:
            awx.showErrorMessage(self)

    def OnOpen(self, event):
        """Open FileDialog to allow the user to select a MDF.nc file."""
        # Show the dialog and retrieve the user response.
        # If it is the OK response, process the data.
        dialog = wx.FileDialog(self, message="Choose a MDF file", defaultDir=os.getcwd(),
                               wildcard="MDF Netcdf files (*.nc)|*.nc",
                               style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_CANCEL: return 

        filepath = os.path.abspath(dialog.GetPath())
        self.read_file(filepath)

    def OnFileHistory(self, event):
        fileNum = event.GetId() - wx.ID_FILE1
        filepath = self.file_history.GetHistoryFile(fileNum)
        self.read_file(filepath)

    def OnClose(self, event):
        """
        Remove the active tab from the notebook and 
        close the corresponding netcdf file, 
        """
        notebook = self.notebook
        if notebook.GetPageCount() == 0: return
        idx = notebook.GetSelection()
        if idx == -1: return None

        # Close the file
        tab = notebook.GetPage(idx)
        #tab.mdf_file.close()

        # Remove tab.
        notebook.DeletePage(idx)
        notebook.Refresh()
        #notebook.SendSizeEvent()

    def OnExit(self, event):
        """Exits the application."""
        # Close open netcdf files.
        #try:
        #    for index in range(self.notebook.GetPageCount()):
        #        tab = self.notebook.GetPage(index)
        #        try:
        #            tab.mdf_file.close()
        #        except:
        #            pass
        #finally:
        self.Destroy()

    def OnAboutBox(self, event):
        """"Info on the application."""
        awx.makeAboutBox(codename=self.codename, version=self.VERSION,
                         description="", developers="M. Giantomassi")


class MdfFileTab(wx.Panel):
    """Tab showing information on a single MDF file."""
    def __init__(self, parent, mdf_file, **kwargs):
        """
        Args:
            parent:
                parent window.
            mdf_file:
        """
        super(MdfFileTab, self).__init__(parent, -1, **kwargs)
        self.mdf_file = mdf_file

        splitter = wx.SplitterWindow(self, id=-1, style=wx.SP_3D)
        splitter.SetSashGravity(0.95)

        self.qpts_panel = KpointsPanel(splitter, mdf_file.structure, mdf_file.qpoints)

        # Add Python shell
        msg = "MDF_object is accessible via the mdf_file variable. Use mdf_file.<TAB> to access the list of methods."
        msg = marquee(msg, width=len(msg) + 8, mark="#")
        msg = "#"*len(msg) + "\n" + msg + "\n" + "#"*len(msg) + "\n"

        # FIXME <Error>: CGContextRestoreGState: invalid context 0x0
        pyshell = Shell(splitter, introText=msg, locals={"mdf_file": mdf_file})
        splitter.SplitHorizontally(self.qpts_panel, pyshell)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND, 5)
        self.SetSizerAndFit(sizer)

    @property
    def statusbar(self):
        return self.viewer_frame.statusbar

    @property
    def viewer_frame(self):
        """The parent frame `MdfViewerFrame`."""
        try:
            return self._viewer_frame
                                                                                    
        except AttributeError:
            self._viewer_frame = self.getParentWithType(MdfViewerFrame)
            return self._viewer_frame


class MdfViewerApp(awx.App):
    def OnInit(self):
        return True

    #def MacOpenFile(self, filepath):
    #    """Called for files droped on dock icon, or opened via finders context menu"""
    #    if filepath.endswith(".py"): return
    #    # Open filename in a new frame.
    #    #logger.info("%s dropped on app %s" % (filename, self.appname))
    #    MdfViewerFrame(parent=None, filepaths=filepath).Show()


def wxapp_mdfviewer(mdf_filepaths):
    app = MdfViewerApp()
    frame = MdfViewerFrame(None, filepaths=mdf_filepaths)
    app.SetTopWindow(frame)
    frame.Show()
    return app


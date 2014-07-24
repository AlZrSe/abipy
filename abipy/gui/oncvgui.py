#!/usr/bin/env python
from __future__ import print_function, division

import os
import copy
import wx
import awx
import pymatgen.core.periodic_table as periodic_table

import wx.lib.mixins.listctrl as listmix
from collections import OrderedDict
from abipy.tools import AttrDict
from abipy.gui.awx.panels import RowMultiCtrl, TableMultiCtrl
from abipy.gui.editor import SimpleTextViewer
from abipy.gui.oncv_tooltips import oncv_tip
from pseudo_dojo.ppcodes.ppgen import OncvGenerator

#def path_img(filename):
#    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", filename)


class OncvApp(wx.App):

    def OnInit(self):
        # The code for the splash screen.
        #image = wx.Image(path_img("wabi_logo.png"), wx.BITMAP_TYPE_PNG)
        #    bmp = image.ConvertToBitmap()
        #    wx.SplashScreen(bmp, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 1000, None, -1)
        #    wx.Yield()
        frame = OncvFrame(None)
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


class OncvFrame(wx.Frame):

    def __init__(self, parent):
        """
        Args:
            parent:
                parent window.
        """
        super(OncvFrame, self).__init__(parent, -1, "Oncvpsp GUI")

        # This combination of options for config seems to work on my Mac.
        self.config = wx.FileConfig(appName=self.codename, localFilename=self.codename + ".ini", 
                                    style=wx.CONFIG_USE_LOCAL_FILE)

        # Build menu, toolbar and status bar.
        self.SetMenuBar(self.makeMenu())
        self.makeToolBar()
        self.statusbar = self.CreateStatusBar()
        #self.statusbar.PushStatusText(message)
        self.Centre()

        self.BuildUI()

    @property
    def codename(self):
        """Name of the application."""
        return "oncvgui"

    def BuildUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        oncv_dims = dict(nc=1, nv=2, lmax=1, ncfn=0)
        # The panel to specify the input variables.
        self.input_panel = OncvInputPanel(self, oncv_dims)
        main_sizer.Add(self.input_panel)

        #run_button = wx.Button(self, -1, label='Run Input')
        #run_button.Bind(wx.EVT_BUTTON, self.OnRunButton)

        self.SetSizerAndFit(main_sizer)

        # The panel to interact with the pseudogenerators.
        frame = awx.Frame(self, title="Pseudopotential Generators")
        self.psgen_panel = PseudoGeneratorsPanel(frame)
        frame.Show()

    def AddFileToHistory(self, filepath):
        """Add the absolute filepath to the file history."""
        self.file_history.AddFileToHistory(filepath)
        self.file_history.Save(self.config)
        self.config.Flush()

    def OnFileHistory(self, event):
        fileNum = event.GetId() - wx.ID_FILE1
        filepath = self.file_history.GetHistoryFile(fileNum)
        self.file_history.AddFileToHistory(filepath)
        #newpanel = OncvInputPanel.from_file(filepath)

    #def OnRunButton(self, event):
    #    """
    #    Called when Run button is pressed.
    #    Run the calculation in a subprocess in non-blocking mode and add it to
    #    the list containing the generators in executions
    #    """
    #    # Build the input file from the values given in the panel.
    #    input_str = self.input_panel.makeInputString()

    #    # Build the PseudoGenerator and run it
    #    psgen = OncvGenerator(input_str, calc_type=self.input_panel.get_calc_type())
    #    psgen.start()
    #    #psgen.wait()

    #    # Add it to the list ctrl.
    #    self.psgen_panel.add_psgen(psgen)

    def _onOptimize_key(self, key):
        template = self.input_panel.makeInput()

        # Build the PseudoGenerator and run it.
        # Note how we select the method to call from key.
        psgens = []
        method = getattr(template, "optimize_" + key)
        for inp in method():
            psgen = OncvGenerator(str(inp), calc_type=self.input_panel.get_calc_type())
            psgens.append(psgen)

        PseudoGeneratorsFrame(self, psgens).Show()

    def OnOptimizeVloc(self, event):
        self._onOptimize_key("vloc")

    def OnOptimizeRhom(self, event):
        self._onOptimize_key("modelcore")

    def makeMenu(self):
        """Creates the main menu."""
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "&Open", help="Open an input file")
        #file_menu.Append(wx.ID_CLOSE, "&Close", help="Close the file associated to the active tab")
        #file_menu.Append(wx.ID_EXIT, "&Quit", help="Exit the application")

        file_history = self.file_history = wx.FileHistory(8)
        file_history.Load(self.config)
        recent = wx.Menu()
        file_history.UseMenu(recent)
        file_history.AddFilesToMenu()
        file_menu.AppendMenu(-1, "&Recent Files", recent)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        menu_bar.Append(file_menu, "File")

        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "About " + self.codename, help="Info on the application")
        menu_bar.Append(help_menu, "Help")

        # Associate menu/toolbar items with their handlers.
        menu_handlers = [
            (wx.ID_OPEN, self.OnOpen),
            #(wx.ID_CLOSE, self.OnClose),
            #(wx.ID_EXIT, self.OnExit),
            (wx.ID_ABOUT, self.OnAbout),
        ]
                                                            
        for combo in menu_handlers:
            mid, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id=mid)

        return menu_bar

    def makeToolBar(self):
        """Creates the toolbar."""
        self.toolbar = toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize(wx.Size(48, 48))

        def bitmap(path):
            return wx.Bitmap(awx.path_img(path))

        self.ID_SHOW_INPUT = wx.NewId()
        self.ID_ADD_TO_QUEUE = wx.NewId()
        self.ID_OPTIMIZE_VLOC = wx.NewId()
        self.ID_OPTIMIZE_RHOM = wx.NewId()

        toolbar.AddSimpleTool(self.ID_SHOW_INPUT, bitmap("in.png"), "Visualize the input file(s) of the workflow.")
        toolbar.AddSimpleTool(self.ID_ADD_TO_QUEUE, bitmap("in.png"), "Add to the queue of pseudos to be generated.")
        toolbar.AddSimpleTool(self.ID_OPTIMIZE_VLOC, bitmap("in.png"), "Optimize the parameters for Vloc for the given template.")
        toolbar.AddSimpleTool(self.ID_OPTIMIZE_RHOM, bitmap("in.png"), "Optimize the parameters for the model charge.")

        toolbar.Realize()

        # Associate menu/toolbar items with their handlers.
        menu_handlers = [
            (self.ID_SHOW_INPUT, self.OnShowInput),
            (self.ID_ADD_TO_QUEUE, self.onAddToQueue),
            (self.ID_OPTIMIZE_VLOC, self.OnOptimizeVloc),
            (self.ID_OPTIMIZE_RHOM, self.OnOptimizeRhom),
        ]

        for combo in menu_handlers:
            mid, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id=mid)

    def OnShowInput(self, event):
        """Show the input file in a new frame."""
        text = self.input_panel.makeInputString()
        SimpleTextViewer(self, text=text).Show()

    def onAddToQueue(self, event):
        """Build a new generator from the input file, and add it to the queue."""
        inp = self.input_panel.makeInputString()
        psgen = OncvGenerator(str(inp), calc_type=self.input_panel.get_calc_type())
        #psgens.append(psgen)

    def OnOpen(self, event):
        dialog = wx.FileDialog(self, message="Choose an inputfile", defaultDir=os.getcwd(),
                               style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)

        # Show the dialog and retrieve the user response. 
        # If it is the OK response, process the data.
        if dialog.ShowModal() == wx.ID_CANCEL: return 

        filepath = dialog.GetPath()
        dialog.Destroy()

        # Add to the history.
        self.file_history.AddFileToHistory(filepath)
        self.file_history.Save(self.config)
        self.config.Flush()

        #newpanel = OncvInputPanel.from_file(filepath)

    #def OnClose(self, event):
    #    """ Respond to the "Close" menu command."""
    #    self.Destroy()

    def OnAbout(self, event):
        description = "oncvgui is a front-end for the pseudopotential generator oncvpsp"

        licence = (
"""OncvGui is free software; you can redistribute
it and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

OncvGui is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. You should have
received a copy of the GNU General Public License along with File OncvGui;
if not, write to the Free Software Foundation, Inc., 59 Temple Place,
Suite 330, Boston, MA  02111-1307  USA""")

        info = wx.AboutDialogInfo()

        #info.SetIcon(wx.Icon(path_img("wabi_logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName('OncvpspsGui')
        info.SetVersion('0.1')
        info.SetDescription(description)
        info.SetCopyright('(C) 2014 Matteo Giantomassi')
        info.SetWebSite("http://www.mat-simresearch.com/")
        info.SetLicence(licence)
        info.AddDeveloper('Matteo Giantomassi')
        wx.AboutBox(info)


def empty_field(tag, oncv_dims):
    """Returns an empty field."""
    # Get the subclass from tag, initialize data with None and call __init__
    cls = _FIELD_LIST[tag]
    data = cls.make_empty_data(oncv_dims)
    return cls(tag, data, oncv_dims)


class Field(object):
    # Flags used to define the type of field
    # Subclasses should define the class attribute type
    FTYPE_ROW = 1
    FTYPE_TABLE = 2
    FTYPE_RAGGED = 3

    # TODO: Change convention cbox --> slist
    parser_for_dtype = dict(
        i=int,
        f=float,
        cbox=str,
    )

    def __init__(self, tag, data, oncv_dims):
        """
        Args:

            tag:
                Tag used to identify the field.
            data:
                Accepts Ordered dict or List of ordered dicts with varname=value.

            oncv_dims:
                Dictionary with all the dimensions of the calculation.
        """
        #print("tag", tag, "data", data, "oncv_dims", oncv_dims)
        self.oncv_dims = AttrDict(**oncv_dims)
        self.tag = tag
        self.data = data

    @classmethod
    def make_empty_data(cls, oncv_dims):
        if cls.ftype == cls.FTYPE_ROW:
            data = OrderedDict([(k, None) for k in cls.WXCTRL_PARAMS.keys()])

        elif cls.ftype == cls.FTYPE_TABLE:
            nrows = cls.nrows_from_dims(oncv_dims)
            data = nrows * [None]
            for i in range(nrows):
                data[i] = OrderedDict([(k, None) for k in cls.WXCTRL_PARAMS.keys()])

        else:
            #print(cls, cls.ftype)
            raise NotImplementedError()

        return data

    @property
    def nrows(self):
        """
        Number of rows i.e. the number of lines in the section
        as specified in the input file.
        """
        if self.ftype == self.FTYPE_ROW:
            return 1
        elif self.ftype == self.FTYPE_TABLE:
            return len(self.data)
        else:
            raise NotImplementedError()

    #@property
    #def cols_per_row(self):
    #    if self.type == self.FTYPE_RAGGED:
    #    raise NotImplementedError()

    def __str__(self):
        """Returns a string with the input variables."""
        lines = []
        app = lines.append

        # Some fields have a single row but we need a list in the loop below.
        entries = self.data
        if self.ftype == self.FTYPE_ROW:
            entries = [self.data]

        for i, entry in enumerate(entries):
            #print(entry)
            if i == 0:  
            # Put comment with the name of the variables only once.
                app("# " + " ".join((str(k) for k in entry.keys())))
            app(" ".join(str(v) for v in entry.values()))

        return "\n".join(lines)

    def has_var(self, key):
        """Return True if variable belongs to self."""
        if self.ftype == self.FTYPE_ROW:
            return key in self.data
        else:
            return key in self.data[0]

    def set_var(self, key, value):
        assert self.has_var(key)
        if self.ftype == self.FTYPE_ROW:
            self.data[key] = value

        elif self.ftype == self.FTYPE_TABLE:
            for r in range(self.nrows):
                self.data[r][key] = value

        else:
            raise NotImplementedError()

    def set_vars(self, ord_vars):
        """
        Set the value of the variables inside a field

        Args:
            ord_vars:
                OrderedDict or list of OrderedDict (depending on field_idx).
        """
        assert len(ord_vars) == len(self.data)

        if self.ftype == self.FTYPE_ROW:
            #assert isinstance(ord_vars, OrderedDict)
            for k, v in ord_vars.items():
                self.data[k] = v

        elif self.ftype == self.FTYPE_TABLE:
            # List of ordered dicts.
            for i, od in enumerate(ord_vars):
                for k, v in od.items():
                    self.data[i][k] = v

        else:
            raise NotImplementedError()

    def set_vars_from_lines(self, lines):
        """The the value of the variables from a list of strings."""
        # TODO: Check this
        #print("About to read: ", type(self))
        #print("\n".join(lines))

        okeys = self.WXCTRL_PARAMS.keys()
        odtypes = [v["dtype"] for v in self.WXCTRL_PARAMS.values()]
        parsers = [self.parser_for_dtype[ot] for ot in odtypes]
        #print("okeys", okeys)
        #print("odtypes", odtypes)

        if self.ftype == self.FTYPE_ROW:
            #print(lines)
            assert len(lines) == 1
            tokens = lines[0].split()
            #print("row tokens", tokens)

            for key, p, tok in zip(okeys, parsers, tokens):
                self.data[key] = p(tok)

        elif self.ftype == self.FTYPE_TABLE:
            assert len(lines) == self.nrows
            for i in range(self.nrows):
                tokens = lines[i].split()
                #print("table tokens: ", tokens)
                for key, p, tok in zip(okeys, parsers, tokens):
                    self.data[i][key] = p(tok)

        else:
            raise NotImplementedError()

    def get_vars(self):
        return self.data

    @classmethod
    def from_wxctrl(cls, wxctrl, tag, oncv_dims):
        # Get the variables from the controller
        ord_vars = wxctrl.GetParams()
        # Build empty field and set its variables.
        new = empty_field(tag, oncv_dims)
        new.set_vars(ord_vars)

        return new

    def make_wxctrl(self, parent, **kwargs):
        """"Build th wx controller associated to this field."""
        if self.ftype == self.FTYPE_ROW:
            return RowMultiCtrl(parent, self._customize_wxctrl(**kwargs))

        elif self.ftype == self.FTYPE_TABLE:
            return TableMultiCtrl(parent, self.nrows, self._customize_wxctrl(**kwargs))

        else:
            # Ragged case e.g. test configurations:
            #dims
            raise NotImplementedError()

    def _customize_wxctrl(self, **kwargs):
        """
        Start with the default parameters for the wx controller
        and override them with those given in kwargs
        """
        # Make a deep copy since WXTRL_PARAMS is mutable.
        import copy
        ctrl_params = copy.deepcopy(self.WXCTRL_PARAMS)

        for label, params in ctrl_params.items():
            value = kwargs.pop("label", None)
            if value is not None:
                params["value"] = str(value)

        return ctrl_params


class RowField(Field):
    """A field made of a single row."""
    ftype = Field.FTYPE_ROW


class TableField(Field):
    """
    A field made of multiple rows, all with the same number of columns
    """
    ftype = Field.FTYPE_TABLE

    @classmethod
    def nrows_from_dims(cls, oncv_dims):
        """Return the number of rows from a dictionary with the dimensions."""
        raise NotImplementedError("Subclasses should define nrows_from_dims")


class RaggedField(Field):
    """
    A field made of ragged rows, i.e. multiple rows with different number of columns.
    """
    ftype = Field.FTYPE_RAGGED

    @classmethod
    def nrows_from_dims(cls, oncv_dims):
        """Return the number of rows from a dictionary with the dimensions."""
        raise NotImplementedError("Subclasses should define nrows_from_dims")

    @classmethod
    def ncols_of_rows(cls, oncv_dims):
        """Return the number of columns in each row from a dictionary with the dimensions."""
        raise NotImplementedError("Subclasses should define nrows_from_dims")


def add_tooltips(cls):
    """Class decorator that add tooltips to WXCTRL_PARAMS."""
    d = cls.WXCTRL_PARAMS
    for key, params in d.items():
        params["tooltip"] = oncv_tip(key)

    return cls


@add_tooltips
class AtomConfField(RowField):
    name = "ATOMIC CONFIGURATION"

    WXCTRL_PARAMS = OrderedDict([
        ("atsym", dict(dtype="cbox", choices=periodic_table.all_symbols())),
        ("z", dict(dtype="i")),
        ("nc", dict(dtype="i", tooltip="number of core states"),),
        ("nv", dict(dtype="i", tooltip="number of valence states")),
        ("iexc", dict(dtype="i", value="4", tooltip="xc functional")),
        ("psfile", dict(dtype="cbox", choices=["psp8", "upf"]))])


@add_tooltips
class RefConfField(TableField):
    name = "REFERENCE CONFIGURATION"

    WXCTRL_PARAMS = OrderedDict([
        ("n", dict(dtype="i")),
        ("l", dict(dtype="i")),
        ("f", dict(dtype="f"))])

    @classmethod
    def nrows_from_dims(cls, oncv_dims):
        return oncv_dims["nv"] + oncv_dims["nc"]

    @property
    def nrows(self):
        return self.oncv_dims["nv"] + self.oncv_dims["nc"]


@add_tooltips
class PseudoConfField(TableField):
    name = "PSEUDOPOTENTIAL AND OPTIMIZATION"

    WXCTRL_PARAMS = OrderedDict([
        ("l", dict(dtype="i")),
        ("rc", dict(dtype="f")),
        ("ep", dict(dtype="f")),
        ("ncon", dict(dtype="i")),
        ("nbas", dict(dtype="i")),
        ("qcut", dict(dtype="f"))])

    @classmethod
    def nrows_from_dims(cls, oncv_dims):
        return oncv_dims["lmax"] + 1

    @property
    def nrows(self):
        return self.oncv_dims["lmax"] + 1


@add_tooltips
class LmaxField(RowField):
    name = "LMAX"

    WXCTRL_PARAMS = OrderedDict([
        ("lmax", dict(dtype="i"))])


@add_tooltips
class VlocalField(RowField):
    name = "LOCAL POTENTIAL"

    WXCTRL_PARAMS = OrderedDict([
        ("lloc", dict(dtype="i")),
        ("lpopt", dict(dtype="i")),
        ("rc5", dict(dtype="f")),
        ("dvloc0", dict(dtype="f"))])


@add_tooltips
class VkbConfsField(TableField):
    name = "VANDERBILT-KLEINMAN-BYLANDER PROJECTORs"

    WXCTRL_PARAMS = OrderedDict([
        ("l", dict(dtype="i")),
        ("nproj", dict(dtype="i", value="2")),
        ("debl", dict(dtype="f"))])

    @classmethod
    def nrows_from_dims(cls, oncv_dims):
        return oncv_dims["lmax"] + 1

    @property
    def nrows(self):
        return self.oncv_dims["lmax"] + 1


@add_tooltips
class ModelCoreField(RowField):
    name = "MODEL CORE CHARGE"

    WXCTRL_PARAMS = OrderedDict([
        ("icmod", dict(dtype="i", value="0")),
        ("fcfact", dict(dtype="f", value="0.0"))])


@add_tooltips
class LogDerField(RowField):
    name = "LOG DERIVATIVE ANALYSIS"

    WXCTRL_PARAMS = OrderedDict([
        ("epsh1", dict(dtype="f", value="-2.0")),
        ("epsh2", dict(dtype="f", value="+2.0")),
        ("depsh", dict(dtype="f", value="0.02"))])


@add_tooltips
class RadGridField(RowField):
    name = "OUTPUT GRID"

    WXCTRL_PARAMS = OrderedDict([
        ("rlmax", dict(dtype="f", value="4.0")),
        ("drl", dict(dtype="f", value="0.01"))])


#@add_tooltips
#class TestConfsField(RaggedField):
    #    name = "TEST CONFIGURATIONS"
    #    WXCTRL_PARAMS = OrderedDict([
    #        ("rlmax", dict(dtype="f", value="4.0")),
    #        ("drl", dict(dtype="f", value="0.01"))])

    #@classmethod
    #def nrows_from_dims(cls, oncv_dims):
    #    return oncv_dims["ncnf"]

    #@property
    #def nrows(self):
    #    return self.oncv_dims["ncnf"] + 1


# List with the field in the same order as the one used in the input file.
_FIELD_LIST = [
    AtomConfField,
    RefConfField,
    LmaxField,
    PseudoConfField,
    VlocalField,
    VkbConfsField,
    ModelCoreField,
    LogDerField,
    RadGridField,
    #TestConfsField,
]

_NFIELDS = len(_FIELD_LIST)


class OncvInput(object):
    """
    This object stores the variables needed for generating a pseudo with oncvsps.
    One can initialize this object either from a prexisting file
    or programmatically from the input provided by the user in a GUI.

    An input consistst of _NFIELDS fields. Each field is either a OrderedDict
    or a list of ordered dicts with the input variables.
    """
    @classmethod
    def from_file(cls, filepath):
        """Initialize the object from an external file."""
        # Read input lines: ignore empty lines or line starting with #
        lines = []
        with open(filepath) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)

        # Read dimensions
        # nc and nv from the first line.
        tokens = lines[0].split()
        atsym, z, nc, nv = tokens[0:4]
        z, nc, nv = map(int, (z, nc, nv))

        # Read lmax and ncfn
        lmax = int(lines[nc + nv + 1])

        # TODO
        # number of tests and number of rows for the different configurations.
        ncnf = 0

        # Initialize the object
        oncv_dims = dict(atsym=atsym, nc=nc, nv=nv, lmax=lmax, ncnf=ncnf)
        inp = OncvInput(oncv_dims)

        # TODO
        # Fill it
        start = 0
        for field in inp:
            stop = start + field.nrows
            field.set_vars_from_lines(lines[start:stop])
            start = stop

        return inp

    def __init__(self, oncv_dims):
        """
        Initialize the object from a dict with the fundamental dimensions.

        """
        self.dims = AttrDict(**oncv_dims)
        #print("oncv_dims", self.dims)

        self.fields = _NFIELDS * [None]

        for tag in range(_NFIELDS):
            new = empty_field(tag, self.dims)
            self.fields[tag] = new

        # 1) ATOM CONFIGURATION
        # atsym, z, nc, nv, iexc   psfile
        # O    8     1   2   3   psp8
        #
        # 2) REFERENCE CONFIGURATION
        # n, l, f  (nc+nv lines)
        # 1    0    2.0
        # 2    0    2.0
        # 2    1    4.0
        #
        # 3) LMAX FIELD
        # lmax
        # 1
        # 4) PSEUDOPOTENTIAL AND OPTIMIZATION
        # l, rc, ep, ncon, nbas, qcut  (lmax+1 lines, l's must be in order)
        # 0    1.60    0.00    4    7    8.00
        # 1    1.60    0.00    4    7    8.00
        #
        # 5) LOCAL POTENTIAL
        # lloc, lpopt, rc(5), dvloc0
        # 4    5    1.4    0.0
        #
        # 6) VANDERBILT-KLEINMAN-BYLANDER PROJECTORs
        # l, nproj, debl  (lmax+1 lines, l's in order)
        # 0    2    1.50
        # 1    2    1.00
        #
        # 7) MODEL CORE CHARGE
        # icmod, fcfact
        # 0    0.0
        #
        # 8) LOG DERIVATIVE ANALYSIS
        # epsh1, epsh2, depsh
        # -2.0  2.0  0.02
        #
        # 9) OUTPUT GRID
        # rlmax, drl
        # 4.0  0.01

        # TODO
        # 10) TEST CONFIGURATIONS
        # ncnf
        # 2
        # nvcnf    (repeated ncnf times)
        # n, l, f  (nvcnf lines, repeated follwing nvcnf's ncnf times)
        # 2
        # 2    0    2.0
        # 2    1    3.0
        #
        # 2
        # 2    0    1.0
        # 2    1    4.0
        #ncnf = 2
        #nvcnf = 2

    @property
    def lmax(self):
        return self.dims.lmax

    def __iter__(self):
        return self.fields.__iter__()

    def __str__(self):
        """Returns a string with the input variables."""
        s =  "\n".join(str(field) for field in self)
        # FIXME needed to bypass problems with tests
        return s + "\n 0"

    def __setitem__(self, key, value):
        ncount = 0
        for f in self.fields:
            if f.has_var(key):
                ncount += 1
                f.set_var(key, value)

        assert ncount == 1

    def deepcopy(self):
        """Deep copy of the input."""
        return copy.deepcopy(self)

    def optimize_vloc(self):
        """
        Produce a list of new input files by changing the lloc option for vloc.
        """
        # Test all possible vloc up to lmax
        inps, new = [], self.deepcopy()
        for il in range(self.lmax+1):
            new["lloc"] = il
            inps.append(new.deepcopy())

        # Add smooth polynomial
        new["lloc"] = 4
        inps.append(new)

        return inps

    def optimize_modelcore(self):
        """
        Produce a list of new input files by changing the icmod option for model core.
        """
        inps, new = [], self.deepcopy()
        for icmod in [0, 1]:
            new["icmod"] = icmod
            inps.append(new.deepcopy())

        return inps


class OncvInputPanel(awx.Panel):
    """
    Panel with widgets for selecting the input parameters.
    """
    def __init__(self, parent, oncv_dims):
        """
        Args:
            oncv_dims:
                Basic dimensions of the calculation.
        """
        super(OncvInputPanel, self).__init__(parent)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        calc_type_label = wx.StaticText(self, -1, "Calculation type:")
        choices = ["scalar-relativistic", "fully-relativistic", "non-relativistic"]
        self.calctype_cbox = wx.ComboBox(
            self, id=-1, name='Calculation type', choices=choices, value=choices[0], style=wx.CB_READONLY)

        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(calc_type_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT, 5)
        hbox0.Add(self.calctype_cbox)

        main_addopts = {}
        self.main_sizer.Add(hbox0, **main_addopts)

        sz = self.build_wxctrls(oncv_dims)
        self.main_sizer.Add(sz, **main_addopts)

        self.fill_from_file("08_O.dat")

        self.SetSizerAndFit(self.main_sizer)

    def build_wxctrls(self, oncv_dims):
        self.oncv_dims = oncv_dims
        sizer, sizer_addopts = wx.BoxSizer(wx.VERTICAL), {}

        # We have nfields sections in the input file.
        # Each field has a widget that returns the variables in a dictionary
        self.wxctrls = _NFIELDS * [None]
        for i in range(_NFIELDS):
            f = empty_field(i, oncv_dims)
            wxctrl = f.make_wxctrl(self)
            self.wxctrls[i] = wxctrl
            sbox_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, f.name + ":"), wx.VERTICAL)
            sbox_sizer.Add(wxctrl, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(sbox_sizer, **sizer_addopts)

        return sizer

    def fill_from_file(self, filename):
        """Build a panel from an input file."""
        inp = OncvInput.from_file(filename)
        for field, wxctrl in zip(inp, self.wxctrls):
            wxctrl.SetParams(field.data)

    def get_calc_type(self):
        """"Return a string with the calculation type."""
        return self.calctype_cbox.GetValue()

    def makeInput(self):
        """Build an instance of OncvInput from the data specified in the Wx controllers."""
        inp = OncvInput(self.oncv_dims)
        for tag, field in enumerate(self.wxctrls):
            inp.fields[tag].set_vars(field.GetParams())

        return inp

    def makeInputString(self):
        """Return a string with the input passed to the pp generator."""
        return str(self.makeInput())


class PseudoGeneratorListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    """
    ListCtrl that allows the user to interact with a list of pseudogenerators
    Supports column sorting
    """
    _COLUMNS = ["#", 'status', "max_ecut", "atan_logder_err"]

    def __init__(self, parent, psgens=(), **kwargs):
        """
        Args:
            parent:
                Parent window.
            psgens:
                List of `PseudoGenerator` instances.
        """
        super(PseudoGeneratorListCtrl, self).__init__(parent, id=-1, style=wx.LC_REPORT | wx.BORDER_SUNKEN, **kwargs)

        self.psgens = psgens if psgens else []

        for index, col in enumerate(self._COLUMNS):
            self.InsertColumn(index, col)

        # Used to store the Max width in pixels for the data in the column.
        column_widths = [awx.get_width_height(self, s)[0] for s in self._COLUMNS]

        # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
        self.itemDataMap = {}

        for index, psgen in enumerate(self.psgens):
            entry = self.make_entry(index, psgen)
            self.Append(entry)
            self.SetItemData(index, index)
            self.itemDataMap[index] = entry

            w = [awx.get_width_height(self, s)[0] for s in entry]
            column_widths = map(max, zip(w, column_widths))

        for index, col in enumerate(self._COLUMNS):
            self.SetColumnWidth(index, column_widths[index])

        # Now that the list exists we can init the other base class, see wx/lib/mixins/listctrl.py
        listmix.ColumnSorterMixin.__init__(self, len(self._COLUMNS))

    @staticmethod
    def make_entry(index, psgen):
        entry = [
            "%d\t\t" % index,
            "%s" % psgen.status,
            "%s" % None,
            "%s" % None]
        return entry

    def doRefresh(self):
        column_widths = [awx.get_width_height(self, s)[0] for s in self._COLUMNS]

        for index, psgen in enumerate(self.psgens):
            entry = self.make_entry(index, psgen)
            print("new entry", entry)
            self.SetItemData(index, index)
            self.itemDataMap[index] = entry

            w = [awx.get_width_height(self, s)[0] for s in entry]
            column_widths = map(max, zip(w, column_widths))

        for index, col in enumerate(self._COLUMNS):
            self.SetColumnWidth(index, column_widths[index])

        super(PseudoGeneratorListCtrl, self).Refresh()

    def add_psgen(self, psgen):
        """Add a PseudoGenerator to the list."""
        index = len(self.psgens)
        entry = self.make_entry(index, psgen)
        self.Append(entry)
        self.SetItemData(index, index)
        self.itemDataMap[index] = entry

        # Add it to the list and update column widths
        self.psgens.append(psgen)
        self.doRefresh()

    def GetListCtrl(self):
        """Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py"""
        return self

    def getSelectedPseudoGen(self):
        """
        Returns the PseudoGenerators selected by the user.
        None if no selection has been done.
        """
        # Get selected index, map to index in kpoints and return the kpoint.
        item = self.GetFirstSelected()
        if item == -1: return None
        index = self.GetItemData(item)
        return self.psgens[index]


class PseudoGeneratorsPanel(awx.Panel):
    """
    A panel with a list of pseudogenerators
    Provides popup menus for performing actions.
    """
    def __init__(self, parent, psgens=(), **kwargs):
        """
        Args:
            parent:
                Parent window.
            psgens:
                List of `PseudoGenerator` objects.
        """
        super(PseudoGeneratorsPanel, self).__init__(parent, **kwargs)

        self.psgens = list(psgens)
        self.psgen_list_ctrl = PseudoGeneratorListCtrl(self, psgens)
        self.psgen_list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRightClick)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.psgen_list_ctrl, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SetSizerAndFit(main_sizer)

        run_button = wx.Button(self, -1, label='Run Input')
        run_button.Bind(wx.EVT_BUTTON, self.OnRunButton)

        check_button = wx.Button(self, -1, label='Check Status')
        check_button.Bind(wx.EVT_BUTTON, self.OnCheckButton)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        hsz.AddMany([run_button, check_button])

        main_sizer.Add(hsz, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        #main_sizer.Add(run_button, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.SetSizerAndFit(main_sizer)

    def OnRunButton(self, event):
        """
        Called when Run button is pressed.
        Run the calculation in a subprocess in non-blocking mode and add it to
        the list containing the generators in executions
        """
        for psgen in self.psgens:
            psgen.start()

    def OnCheckButton(self, event):
        for psgen in self.psgens:
            psgen.check_status()

        self.psgen_list_ctrl.doRefresh()

    def add_psgen(self, psgen):
        """Add a new generator to the internal list."""
        self.psgens.append(psgen)
        self.psgen_list_ctrl.add_psgen(psgen)

    def onRightClick(self, event):
        """Generate the popup menu."""
        popup_menu = self.makePopupMenu()
        self.PopupMenu(popup_menu, event.GetPoint())
        popup_menu.Destroy()

    def getSelectedPseudoGen(self):
        return self.psgen_list_ctrl.getSelectedPseudoGen()

    def makePopupMenu(self):
        """
        Build and return a popup menu. Subclasses can extend or replace this base method.
        """
        self.ID_POPUP_PLOT_RESULTS = wx.NewId()
        self.ID_POPUP_STDIN = wx.NewId()
        self.ID_POPUP_STDOUT = wx.NewId()
        self.ID_POPUP_STDERR = wx.NewId()

        menu = wx.Menu()
        menu.Append(self.ID_POPUP_PLOT_RESULTS, "Plot results")
        menu.Append(self.ID_POPUP_STDIN, "Show standard input")
        menu.Append(self.ID_POPUP_STDOUT, "Show standard output")
        menu.Append(self.ID_POPUP_STDERR, "Show standard error")

        # Associate menu/toolbar items with their handlers.
        menu_handlers = [
            (self.ID_POPUP_PLOT_RESULTS, self.onPlotResults),
            (self.ID_POPUP_STDIN, self.onShowStdin),
            (self.ID_POPUP_STDOUT, self.onShowStdout),
            (self.ID_POPUP_STDERR, self.onShowStderr),
        ]

        for combo in menu_handlers:
            mid, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id=mid)

        return menu

    def _showStdfile(self, event, stdfile):
        psgen = self.psgen_list_ctrl.getSelectedPseudoGen()
        if psgen is None: return
        call = dict(
            stdin=psgen.get_stdin,
            stdout=psgen.get_stdout,
            stderr=psgen.get_stderr,
        )[stdfile]

        SimpleTextViewer(self, text=call()).Show()

    def onShowStdin(self, event):
        """Open a frame with the input file."""
        self._showStdfile(event, "stdin")

    def onShowStdout(self, event):
        """Open a frame with the output file."""
        self._showStdfile(event, "stdout")

    def onShowStderr(self, event):
        """Open a frame with the stderr file."""
        self._showStdfile(event, "stderr")

    def onPlotResults(self, event):
        """Plot the results with matplotlib."""
        psgen = self.psgen_list_ctrl.getSelectedPseudoGen()
        if psgen is None: return
        #if psgen.status <= psgen.S_DONE:
        #    print("Cannot plot results since run is not completed")
        #    return
        psgen.plot_results()


class PseudoGeneratorsFrame(awx.Frame):
    def __init__(self, parent, psgens=(), **kwargs):
        super(PseudoGeneratorsFrame, self).__init__(parent, **kwargs)
        self.panel = PseudoGeneratorsPanel(self, psgens)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #main_sizer.Add(self.panel)


if __name__ == "__main__":
    import sys
    onc_inp = OncvInput.from_file("08_O.dat")
    print(onc_inp)
    #sys.exit(0)
    for inp in onc_inp.optimize_vloc():
        print("new\n", inp)

    for inp in onc_inp.optimize_modelcore():
        print("new model\n", inp)

    app = OncvApp()
    app.MainLoop()


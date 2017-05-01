# coding: utf-8
"""Objects to analyze the results stored in the GRUNS.nc file produced by anaddb."""
from __future__ import print_function, division, unicode_literals, absolute_import

import numpy as np
import pymatgen.core.units as pmgu

from collections import OrderedDict
from monty.string import marquee, list_strings
from monty.termcolor import cprint
from monty.collections import AttrDict
from monty.functools import lazy_property
from abipy.core.kpoints import Kpath, IrredZone, KSamplingInfo
from abipy.core.mixins import AbinitNcFile, Has_Structure, Has_ElectronBands, NotebookWriter
from abipy.dfpt.phonons import PhononBands, PhononBandsPlotter
from abipy.iotools import ETSF_Reader
from abipy.tools.plotting import add_fig_kwargs, get_ax_fig_plt, set_axlims
#from abipy.tools import duck


# DOS name --> meta-data
_ALL_DOS_NAMES = OrderedDict([
    ("wdos", dict(latex=r"$DOS$")),
    ("gruns_grdos", dict(latex=r"$DOS_{\gamma}$")),
    ("gruns_gr2dos", dict(latex=r"$DOS_{\gamma^2}$")),
    ("gruns_vdos", dict(latex=r"$DOS_v$")),
    ("gruns_v2dos", dict(latex=r"$DOS_{v^2}$")),
])


class GrunsNcFile(AbinitNcFile, Has_Structure, NotebookWriter):
    """
    This object provides an interface to the `GRUNS.nc` file produced by abinit.
    This file contains Grunesein parameters computed via finite difference.

    Usage example:

    .. code-block:: python

        with GrunsNcFile("foo_GRUNS.nc") as ncfile:
            print(ncfile)
    """
    @classmethod
    def from_file(cls, filepath):
        """Initialize the object from a Netcdf file"""
        return cls(filepath)

    def __init__(self, filepath):
        super(GrunsNcFile, self).__init__(filepath)
        self.reader = GrunsReader(filepath)

    def close(self):
        """Close file."""
        self.reader.close()

    def __str__(self):
        return self.to_string()

    def to_string(self, verbose=0):
        """String representation."""
        lines = []; app = lines.append

        app(marquee("File Info", mark="="))
        app(self.filestat(as_string=True))
        app("")
        app(marquee("Structure", mark="="))
        app(str(self.structure))
        app("")
        if self.phbands_qpath_vol:
            app(self.phbands_qpath_vol[self.iv0].to_string(with_structure=False, title="Phonon Bands at V0"))
        app("")
        app("Number of Volumes: %d" % self.reader.num_volumes)

        return "\n".join(lines)

    @property
    def structure(self):
        """Crystalline structure corresponding to the central point V0."""
        return self.reader.structure

    #@property
    #def volumes(self):
    #    """Volumes of the unit cell in Angstrom**3"""
    #    return self.reader.volumes

    @property
    def iv0(self):
        return self.reader.iv0

    @lazy_property
    def doses(self):
        "Dictionary with the phonon doses."""
        return self.reader.read_doses()

    @lazy_property
    def phbands_qpath_vol(self):
        """List of :class:`PhononBands objects corresponding to the different volumes."""
        return self.reader.read_phbands_on_qpath()

    def to_dataframe(self):
        """
        Return a pandas DataFrame with the following columns:

            ['qidx', 'mode', 'freq', 'qpoint']

        where:

        ==============  ==========================
        Column          Meaning
        ==============  ==========================
        qidx            q-point index.
        mode            phonon branch index.
        grun            Gruneisen parameter.
        groupv          Group velocity.
        freq            Phonon frequency in eV.
        qpoint          :class:`Kpoint` object
        ==============  ==========================
        """
        if "gruns_gvals_qibz" not in self.reader.rootgrp.variables:
            raise RuntimeError("GRUNS.nc file does not contain `gruns_gvals_qibz`."
                               "Use prtdos in anaddb input file to compute these values in the IBZ")

        grun_vals = self.reader.read_value("gruns_gvals_qibz")
        phfreqs = self.reader.rootgrp.variables["gruns_wvols_qibz"][:, self.iv0, :]
        #dwdq = self.reader.read_value("gruns_dwdq_qibz")
        #groupv =
        nqibz, natom3 = grun_vals.shape
        print("nqibz", nqibz, "natom3", natom3)

        import pandas as pd
        rows = []
        for iq in range(nqibz):
            for nu in range(natom3):
                rows.append(OrderedDict([
                           ("qidx", iq),
                           ("mode", nu),
                           ("grun", grun_vals[iq, nu]),
                           #("groupv", groupv[iq, nu]),
                           ("freq", phfreqs[iq, nu]),
                           #("qpoint", self.qpoints[iq]),
                        ]))

        return pd.DataFrame(rows, columns=list(rows[0].keys()))

    @add_fig_kwargs
    def plot_doses(self, xlims=None, dos_names="all", with_idos=True, **kwargs):
        """
        Plot the different doses stored in the GRUNS file.

        Args:
            xlims: Set the data limits for the x-axis in eV. Accept tuple e.g. `(left, right)`
                or scalar e.g. `left`. If left (right) is None, default values are used
            dos_names: List of strings defining the DOSes to plot. Use `all` to plot all DOSes available.
            with_idos: True to display integrated doses
            ax: matplotlib :class:`Axes` or None if a new figure should be created.

        Returns:
            matplotlib figure.
        """
        if not self.doses:
            return None
        #write(unt,'(a)')'# Phonon density of states, Gruneisen DOS and phonon group velocity DOS'
        #write(unt,'(a)')"# Energy in Hartree, DOS in states/Hartree"
        #write(unt,'(a,i0)')'# Tetrahedron method with nqibz= ',nqibz
        #write(unt,"(a,f8.5)")"# Average Gruneisen parameter:", gavg
        #write(unt,'(5a)') &
        #  "# omega PH_DOS Gruns_DOS Gruns**2_DOS Vel_DOS  Vel**2_DOS  PH_IDOS Gruns_IDOS Gruns**2_IDOS Vel_IDOS Vel**2_IDOS"

        dos_names = _ALL_DOS_NAMES.keys() if dos_names == "all" else list_strings(dos_names)
        wmesh = self.doses["wmesh"]

        import matplotlib.pyplot as plt
        nrows = len(dos_names)
        fig, axes = plt.subplots(nrows=nrows, ncols=1, sharex=True, squeeze=False)
        axes = axes.ravel()

        for i, (name, ax) in enumerate(zip(dos_names, axes)):
            dos, idos = self.doses[name][0], self.doses[name][1]
            ax.plot(wmesh, dos, color="k")
            ax.grid(True)
            set_axlims(ax, xlims, "x")
            ax.set_ylabel(_ALL_DOS_NAMES[name]["latex"])
            #ax.yaxis.set_ticks_position("right")

            if with_idos:
                other_ax = ax.twinx()
                other_ax.plot(wmesh, idos, color="k")
                other_ax.set_ylabel(_ALL_DOS_NAMES[name]["latex"].replace("DOS", "IDOS"))

            if i == len(dos_names) - 1:
                ax.set_xlabel(r"$\omega$ [eV]")
            #ax.legend(loc="best")

        return fig

    def get_plotter(self):
        """
        Return an instance of :class:`PhononBandsPlotter` that can be use to plot
        multiple phonon bands or animate the bands
        """
        plotter = PhononBandsPlotter()
        for iv, phbands in enumerate(self.phbands_qpath_vol):
            plotter.add_phbands(str(iv), phbands)

        return plotter

    @add_fig_kwargs
    def plot_phbands_with_gruns(self, gamma_fact=50, with_doses="all", units="eV",
                                ylims=None, match_bands=False, **kwargs):
        """
        Plot the phonon bands corresponding to V0 (the central point) with markers
        showing the value and the sign of the Grunesein parameters.

        Args:
            gamma_fact: Scaling factor for Grunesein parameters.
                Up triangle for positive values, down triangles for negative values.
            with_doses: "all" to plot all DOSes available, `None` to disable DOS plotting,
                else list of strings with the name of the DOSes to plot.
            units: Units for phonon plots. Possible values in ("eV", "meV", "Ha", "cm-1", "Thz"). Case-insensitive.
            ylims: Set the data limits for the x-axis in eV. Accept tuple e.g. `(left, right)`
                or scalar e.g. `left`. If left (right) is None, default values are used
            match_bands: if True tries to follow the band along the path based on the scalar product of the eigenvectors.
            ax: matplotlib :class:`Axes` or None if a new figure should be created.

        Returns:
            matplotlib figure.
        """
        if not self.phbands_qpath_vol: return None
        phbands = self.phbands_qpath_vol[self.iv0]
        factor = phbands.factor_ev2units(units)

        # Build axes (ax_bands and ax_doses)
        if with_doses is None:
            ax_bands, fig, plt = get_ax_fig_plt(ax=None)
        else:
            import matplotlib.pyplot as plt
            from matplotlib.gridspec import GridSpec
            dos_names = list(_ALL_DOS_NAMES.keys()) if with_doses == "all" else list_strings(with_doses)
            ncols = 1 + len(dos_names)
            fig = plt.figure()
            width_ratios = [2] + len(dos_names) * [0.2]
            gspec = GridSpec(1, ncols, width_ratios=width_ratios)
            gspec.update(wspace=0.05)
            ax_bands = plt.subplot(gspec[0])
            ax_doses = []
            for i in range(len(dos_names)):
                ax_doses.append(plt.subplot(gspec[i + 1], sharey=ax_bands))

        # Plot phonon bands.
        phbands.plot(ax=ax_bands, units=units, match_bands=match_bands, show=False)

        # Plot gruneisen markers on top of band structure.
        xvals = np.arange(len(phbands.phfreqs))
        for nu in phbands.branches:
            omegas = phbands.phfreqs[:, nu] * factor
            sizes = phbands.grun_vals[:, nu].copy()

            # Use different symbols depending on the value of s. Cannot use negative s.
            xys = np.array([xos for xos in zip(xvals, omegas, sizes) if xos[2] >= 0]).T.copy()
            if xys.size:
                ax_bands.scatter(xys[0], xys[1], s=xys[2] * gamma_fact, marker="^", label=" >0", color="blue")

            xys = np.array([xos for xos in zip(xvals, omegas, sizes) if xos[2] < 0]).T.copy()
            if xys.size:
                ax_bands.scatter(xys[0], xys[1], s=np.abs(xys[2]) * gamma_fact, marker="v", label=" <0", color="blue")

        set_axlims(ax_bands, ylims, "x")

        if with_doses is None:
            return fig

        # Plot Doses.
        wmesh = self.doses["wmesh"] * factor
        for i, (name, ax) in enumerate(zip(dos_names, ax_doses)):
            dos, idos = self.doses[name][0], self.doses[name][1]
            ax.plot(dos, wmesh, label=name, color="k")
            set_axlims(ax, ylims, "x")
            ax.grid(True)
            ax.set_ylabel("")
            ax.tick_params(labelbottom='off')
            if i == len(dos_names) - 1:
                ax.yaxis.set_ticks_position("right")
            else:
                ax.tick_params(labelleft='off')
            ax.set_title(_ALL_DOS_NAMES[name]["latex"])

        return fig

    def write_notebook(self, nbpath=None):
        """
        Write a jupyter notebook to nbpath. If nbpath is None, a temporay file in the current
        working directory is created. Return path to the notebook.
        """
        nbformat, nbv, nb = self.get_nbformat_nbv_nb(title=None)

        nb.cells.extend([
            nbv.new_code_cell("ncfile = abilab.abiopen('%s')" % self.filepath),
            nbv.new_code_cell("print(ncfile)"),

            nbv.new_code_cell("fig = ncfile.plot_doses()"),
            nbv.new_code_cell("fig = ncfile.plot_phbands_with_gruns()"),

            nbv.new_code_cell("plotter = ncfile.get_plotter()\nprint(plotter)"),
            nbv.new_code_cell("df_phbands = plotter.get_phbands_frame()\ndisplay(df_phbands)"),
            nbv.new_code_cell("plotter.ipw_select_plot()"),

            nbv.new_code_cell("gruns_data = ncfile.to_dataframe()"),
            nbv.new_code_cell("""\
#import df_widgets.seabornw as snsw
#snsw.api_selector(gruns_data)"""),
        ])

        return self._write_nb_nbpath(nb, nbpath)


class GrunsReader(ETSF_Reader):
    """
    This object reads the results stored in the GRUNS file produced by ABINIT.
    It provides helper functions to access the most important quantities.
    """
    # Fortran arrays (remember to transpose dimensions!)
    #nctkarr_t("gruns_qptrlatt", "int", "three, three"), &
    #nctkarr_t("gruns_shiftq", "dp", "three, gruns_nshiftq"), &
    #nctkarr_t("gruns_qibz", "dp", "three, gruns_nqibz"), &
    #nctkarr_t("gruns_wtq", "dp", "gruns_nqibz"), &
    #nctkarr_t("gruns_gvals_qibz", "dp", "number_of_phonon_modes, gruns_nqibz"), &
    #nctkarr_t("gruns_wvols_qibz", "dp", "number_of_phonon_modes, gruns_nvols, gruns_nqibz"), &
    #nctkarr_t("gruns_dwdq_qibz", "dp", "three, number_of_phonon_modes, gruns_nqibz"), &
    #nctkarr_t("gruns_omega_mesh", "dp", "gruns_nomega"), &
    #nctkarr_t("gruns_wdos", "dp", "gruns_nomega, two"), &
    #nctkarr_t("gruns_grdos", "dp", "gruns_nomega, two"), &
    #nctkarr_t("gruns_gr2dos", "dp", "gruns_nomega, two"), &
    #nctkarr_t("gruns_v2dos", "dp", "gruns_nomega, two"), &
    #nctkarr_t("gruns_vdos", "dp", "gruns_nomega, two") &
    #nctkarr_t("gruns_qpath", "dp", "three, gruns_nqpath")
    #nctkarr_t("gruns_gvals_qpath", "dp", "number_of_phonon_modes, gruns_nqpath")
    #nctkarr_t("gruns_wvols_qpath", "dp", "number_of_phonon_modes, gruns_nvols, gruns_nqpath")
    #nctkarr_t("gruns_dwdq_qpath", "dp", "three, number_of_phonon_modes, gruns_nqpath")

    def __init__(self, filepath):
        super(GrunsReader, self).__init__(filepath)

        # Read and store important quantities.
        self.structure = self.read_structure()

        self.num_volumes = self.read_dimvalue("gruns_nvols")
        self.iv0 = 3 - 1  # F --> C
        # TODO
        #self.iv0 = self.read_value("gruns_iv0")

    def read_doses(self):
        """
        Return a :class:`AttrDict` with the DOSes available in the file. Empty dict if
        DOSes are not available.
        """
        if "gruns_nomega" not in self.rootgrp.dimensions:
            cprint("File %s does not contain ph-DOSes, returning empty dict" % self.path, "yellow")
            return {}

        # Read q-point sampling used to compute DOSes.
        qptrlatt = self.read_value("gruns_qptrlatt")
        shifts = self.read_value("gruns_shiftq")
        qsampling = KSamplingInfo.from_kptrlatt(qptrlatt, shifts, kptopt=1)

        frac_coords_ibz = self.read_value("gruns_qibz")
        weights = self.read_value("gruns_wtq")
        qpoints = IrredZone(self.structure.reciprocal_lattice, frac_coords_ibz,
                            weights=weights, names=None, ksampling=qsampling)

        return AttrDict(
            wmesh=self.read_value("gruns_omega_mesh"),
            wdos=self.read_value("gruns_wdos"),
            gruns_grdos=self.read_value("gruns_grdos"),
            gruns_gr2dos=self.read_value("gruns_gr2dos"),
            gruns_v2dos=self.read_value("gruns_v2dos"),
            gruns_vdos=self.read_value("gruns_vdos"),
            qpoints=qpoints,
        )

    def read_phbands_on_qpath(self):
        """
        Return a list of :class:`PhononBands` computed at the different volumes.
        The `iv0` entry corresponds to the central point used to compute Grunesein parameters
        with finite differences. This object stores the Grunesein parameters in `grun_vals`.
        """
        if "gruns_qpath" not in self.rootgrp.variables:
            cprint("File `%s` does not contain phonon bands, returning empty list." % self.path, "yellow")
            return []

        qfrac_coords = self.read_value("gruns_qpath")
        grun_vals = self.read_value("gruns_gvals_qpath")
        freqs_vol = self.read_value("gruns_wvols_qpath")
        dwdw = self.read_value("gruns_dwdq_qpath")

        phbands_qpath_vol = []
        for ivol in range(self.num_volumes):
            # TODO structure depends on vol, non_anal_ph, amu, phdispl_cart ...
            structure = self.structure
            qpoints = Kpath(structure.reciprocal_lattice, qfrac_coords)
            #phdispl_cart = np.zeros(
            phdispl_cart = None
            phb = PhononBands(structure, qpoints, freqs_vol[:, ivol], phdispl_cart, non_anal_ph=None, amu=None)
            # Add grunesein parameters.
            if ivol == self.iv0: phb.grun_vals = grun_vals
            phbands_qpath_vol.append(phb)

        return phbands_qpath_vol

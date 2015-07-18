# coding: utf-8
"""PSPS file with tabulated data."""
from __future__ import print_function, division, unicode_literals

import numpy as np
import pymatgen.core.units as units

from collections import OrderedDict, Iterable, defaultdict
from monty.string import is_string, list_strings
from monty.collections import AttrDict
from monty.functools import lazy_property
from pymatgen.util.plotting_utils import add_fig_kwargs, get_ax_fig_plt
from pymatgen.io.abinitio.pseudos import Pseudo
from abipy.iotools import ETSF_Reader
from abipy.core.mixins import AbinitNcFile, Has_Structure, Has_ElectronBands
from prettytable import PrettyTable


import logging
logger = logging.getLogger(__name__)


def compare_pseudos(filepaths, ecut=30):
    """
    This function receives a list of pseudopotential files, call
    Abinit to produced the PSPS.nc files and produces matplotlib plots
    comparing the behaviour of the pseudos in real and in reciprocal space.

    Args:
        filepaths: List of file names.
        ecut: Cutoff energy for the wavefunctions in Ha.
    """
    pseudos = [Pseudo.from_file(path) for path in filepaths]

    psps_files = [p.open_pspsfile(ecut=ecut) for p in pseudos]

    p0 = psps_files[0]
    p0.compare(psps_files[1:])

    for pfile in psps_files:
        pfile.close()


def mklabel(fsym, der, arg):
    """mklabel(f, 2, x) --> $f''(x)$"""
    if der == 0:
        return "$%s(%s)$" % (fsym, arg)
    else:
        fsym = fsym + "^{" + (der * "\prime") + "}"
        return "$%s(%s)$" % (fsym, arg)


def rescale(arr, scale=1.0):
    if scale is None:
        return arr, 0.0

    max = np.abs(arr).max()
    fact = scale / max if max != 0 else 1
    return  fact * arr, fact


class PspsFile(AbinitNcFile):
    """
    Netcdf file with the tables used in Abinit to apply the 
    pseudopotential part of the KS Hamiltonian. 

    Usage example:
                                                                  
    .. code-block:: python
        
        with PspsFile("foo_PSPS.nc") as psps:
            psps.plot_modelcore_rspace()
    """
    linestyles_der = ["-", "--", '-.', ':', ":", ":"]

    @classmethod
    def from_file(cls, filepath):
        """Initialize the object from a Netcdf file"""
        return cls(filepath)

    def __init__(self, filepath):
        super(PspsFile, self).__init__(filepath)
        self.reader = r = PspsReader(filepath)

    def close(self):
        self.reader.close()

    @add_fig_kwargs
    def plot(self, what="all", **kwargs):
        """
        Driver routine to plot several quantities on the same graph.

        Args:
            what: List of strings selecting the quantities to plot.
                possible values in ["corer", "coreq", "vlocq", "ffspl"]
       
        Return: matplotlb Figure
        """
        if what == "all":
            what = ["corer", "coreq", "vlocq", "ffspl"]
        else:
            what = list_strings(what)

        import matplotlib.pyplot as plt
        fig, ax_list = plt.subplots(nrows=len(what), ncols=1, squeeze=True)

        what2method = {
            "corer": "plot_modelcore_rspace",
            "coreq": "plot_modelcore_qspace",
            "vlocq": "plot_vlspl",
            "ffspl": "plot_ffspl",
        }

        for w, ax in zip(what, ax_list):
            getattr(self, what2method[w])(ax=ax, show=False)

        return fig

    @add_fig_kwargs
    def plot_modelcore_rspace(self, ax=None, ders=(0, 1, 2, 3), rmax=3.0,  **kwargs):
        """
        Plot the model core and its derivatives in real space.

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.
            ders: Tuple used to select the derivatives to be plotted.
            rmax: Max radius for plot in Bohr. None is full grid is wanted.

        Returns:
            matplotlib figure.
        """
        ax, fig, plt = get_ax_fig_plt(ax)

        color = kwargs.pop("color", "black")
        linewidth = kwargs.pop("linewidth", 2.0)

        rmeshes, coresd = self.reader.read_coresd(rmax=rmax)

        for rmesh, mcores in zip(rmeshes, coresd): 
            for der, values in enumerate(mcores):
                if der not in ders: continue
                yvals, fact, = rescale(values)
                ax.plot(rmesh, yvals, color=color, linewidth=linewidth, 
                        linestyle=self.linestyles_der[der], 
                        label=mklabel("\\tilde{n}_c", der, "r") + " x %.4f" % fact)

        ax.grid(True)
        ax.set_xlabel("r [Bohr]")
        ax.set_title("Model core in r-space")
        ax.legend(loc="upper right")

        return fig

    @add_fig_kwargs
    def plot_modelcore_qspace(self, ax=None, ders=(0,), with_fact=False, with_qn=0, **kwargs):
        """
        Plot the model core in q space

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.
            ders: Tuple used to select the derivatives to be plotted.
            with_qn:

        Returns:
            matplotlib figure.
        """
        ax, fig, plt = get_ax_fig_plt(ax)

        color = kwargs.pop("color", "black")
        linewidth = kwargs.pop("linewidth", 2.0)

        qmesh, tcore_spl = self.reader.read_tcorespl()
        ecuts = 2 * (np.pi * qmesh)**2
        lines = []
        for atype, tcore_atype in enumerate(tcore_spl): 
            for der, values in enumerate(tcore_atype):
                if der == 1: der = 2
                if der not in ders: continue
                yvals, fact = rescale(values)

                label = mklabel("\\tilde{n}_{c}", der, "q")
                if with_fact: label += " x %.4f" % fact

                line, = ax.plot(ecuts, yvals, color=color, linewidth=linewidth, 
                                linestyle=self.linestyles_der[der], label=label)
                lines.append(line)

                if with_qn and der == 0:
                    yvals, fact = rescale(qmesh * values)
                    line, ax.plot(ecuts, yvals, color=color, linewidth=linewidth, 
                                  label=mklabel("q f", der, "q") + " x %.4f" % fact)

                    lines.append(line)

        ax.grid(True)
        ax.set_xlabel("Ecut [Hartree]")
        ax.set_title("Model core in q-space")
        ax.legend(loc="upper right")

        return fig

    @add_fig_kwargs
    def plot_vlspl(self, ax=None, ders=(0,), with_qn=0, with_fact=False, **kwargs):
        """
        Plot the local part of the pseudopotential in q space.

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.
            ders: Tuple used to select the derivatives to be plotted.
            with_qn:

        Returns:
            matplotlib figure.
        """
        ax, fig, plt = get_ax_fig_plt(ax)

        color = kwargs.pop("color", "black")
        linewidth = kwargs.pop("linewidth", 2.0)

        qmesh, vlspl = self.reader.read_vlspl()
        ecuts = 2 * (np.pi * qmesh)**2
        for atype, vl_atype in enumerate(vlspl): 
            for der, values in enumerate(vl_atype):
                if der == 1: der = 2
                if der not in ders: continue

                yvals, fact = rescale(values)
                label = mklabel("v_{loc}", der, "q")
                if with_fact: label += " x %.4f" % fact

                ax.plot(ecuts, yvals, color=color, linewidth=linewidth, 
                        linestyle=self.linestyles_der[der], label=label)

                if with_qn and der == 0:
                    yvals, fact = rescale(qmesh * values)
                    ax.plot(ecuts, yvals, color=color, linewidth=linewidth, 
                            label="q*f(q) x %2.f" % fact)

        ax.grid(True)
        ax.set_xlabel("Ecut [Hartree]")
        ax.set_title("Vloc(q)")
        ax.legend(loc="upper right")

        return fig

    @add_fig_kwargs
    def plot_ffspl(self, ax=None, ders=(0,), with_qn=0, with_fact=False, **kwargs):
        """
        Plot the nonlocal part of the pseudopotential in q space.

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.
            ders: Tuple used to select the derivatives to be plotted.
            with_qn:

        Returns:
            matplotlib figure.
        """
        ax, fig, plt = get_ax_fig_plt(ax)

        color = kwargs.pop("color", "black")
        linewidth = kwargs.pop("linewidth", 2.0)

        color_l = {-1: "black", 0: "red", 1: "blue", 2: "green", 3: "orange"}
        linestyles_n = ["solid", '-', '--', '-.', ":"]
        scale = None

        all_projs = self.reader.read_projectors()
        for itypat, projs_type in enumerate(all_projs): 
            # Loop over the projectors for this atom type.
            for p in projs_type:
                for der, values in enumerate(p.data):
                    if der == 1: der = 2
                    if der not in ders: continue
                    #yvals, fact = rescale(values, scale=scale)
                    label = mklabel("v_{nl}", der, "q")
                    ax.plot(p.ecuts, values * p.ekb, color=color_l[p.l], linewidth=linewidth, 
                            linestyle=linestyles_n[p.n]) #, label=label)

        ax.grid(True)
        ax.set_xlabel("Ecut [Hartree]")
        ax.set_title("ekb * ffnl(q)")
        #ax.legend(loc="upper right")

        return fig

    @add_fig_kwargs
    def compare(self, others, what="all", **kwargs):
        if not isinstance(others, (list, tuple)):
            others = [others]

        if what == "all":
            what = ["corer", "coreq", "vlocq", "ffspl"]
        else:
            what = list_strings(what)

        import matplotlib.pyplot as plt
        fig, ax_list = plt.subplots(nrows=len(what), ncols=1, squeeze=True)

        def mkcolor(count):
            npseudos = 1 + len(others)
            if npseudos <= 2:
                return {0: "red", 1: "blue"}[count]
            else:
                cmap = plt.get_cmap("jet")
                return cmap(float(count)/ (1 + len(others)))

        ic = -1
        if "corer" in what:
            ic += 1; ax = ax_list[ic]
            self.plot_modelcore_rspace(ax=ax, color=mkcolor(0), show=False)
            for count, other in enumerate(others):
                other.plot_modelcore_rspace(ax=ax, color=mkcolor(count+1), show=False)

        if "coreq" in what:
            ic += 1; ax = ax_list[ic]
            self.plot_modelcore_qspace(ax=ax, with_qn=0, color=mkcolor(0), show=False)
            for count, other in enumerate(others):
                other.plot_modelcore_qspace(ax=ax, with_qn=0, color=mkcolor(count+1), show=False)

        if "vlocq" in what:
            ic += 1; ax = ax_list[ic]
            self.plot_vlspl(ax=ax, with_qn=0, color=mkcolor(0), show=False)
            for count, other in enumerate(others):
                other.plot_vlspl(ax=ax, with_qn=0, color=mkcolor(count+1), show=False)

        if "ffspl" in what:
            ic += 1; ax = ax_list[ic]
            self.plot_ffspl(ax=ax, with_qn=0, color=mkcolor(0), show=False)
            for count, other in enumerate(others):
                other.plot_ffspl(ax=ax, with_qn=0, color=mkcolor(count+1), show=False)

        return fig


class PspsReader(ETSF_Reader):
    """
    This object reads the results stored in the _GSR (Ground-State Results) file produced by ABINIT.
    It provides helper function to access the most important quantities.
    """
    def __init__(self, filepath):
        super(PspsReader, self).__init__(filepath)

        # Get important quantities.
        self.usepaw, self.useylm = self.read_value("usepaw"), self.read_value("useylm")
        assert self.usepaw == 0 and self.useylm == 0
        self.ntypat = self.read_dimvalue("ntypat") 
        self.lmnmax = self.read_dimvalue("lmnmax")
        self.indlmn = self.read_value("indlmn")

        self.znucl_typat = self.read_value("znucltypat")
        self.zion_typat = self.read_value("ziontypat")

        # TODO
        #self.psps_files = []
        #for strng in r.read_value("filpsp"):
        #    s = "".join(strng)
        #    print(s)
        #    self.psps_files.append(s)
        #print(self.psps_files)

    def read_coresd(self, rmax=None):
        """
        Read the core charges and derivatives for the different types of atoms.

        Args:
            rmax: Maximum radius in Bohr. If None, data on the full grid is returned.

        Returns:
            meshes: List of ntypat arrays. Each array contains the linear meshes in real space.
            coresd: List with nytpat arrays of shape [6, npts].

        xccc1d[ntypat6,n1xccc*(1-usepaw)]

        Norm-conserving psps only
        The component xccc1d(n1xccc,1,ntypat) is the pseudo-core charge
        for each type of atom, on the radial grid. The components
        xccc1d(n1xccc,ideriv,ntypat) give the ideriv-th derivative of the
        pseudo-core charge with respect to the radial distance.
        """
        # TODO
        # model core may not be present!
        xcccrc = self.read_value("xcccrc") 
        all_coresd = self.read_value("xccc1d") 

        npts = all_coresd.shape[-1]
        rmeshes, coresd = [], []
        for itypat, rc in enumerate(xcccrc):
            rvals, step = np.linspace(0, rc, num=npts, retstep=True)
            ir_stop = -1
            if rmax is not None: 
                # Truncate mesh
                ir_stop = min(int(rmax / step), npts) + 1
                #print(rmax, step, ir_stop, npts)

            rmeshes.append(rvals[:ir_stop])
            coresd.append(all_coresd[itypat, :, :ir_stop])

        return rmeshes, coresd

    def read_tcorespl(self):
        """
        Returns:
            qmesh: Linear q-mesh in G-space
            tcorespl:

        tcorespl[ntypat, 2, mqgrid_vl]
        Gives the pseudo core density in reciprocal space on a regular grid. 
        Only if has_tcore
        """
        return self.read_value("qgrid_vl"), self.read_value("nc_tcorespl")

    def read_vlspl(self):
        """
        Returns:
            qmesh: Linear q-mesh in G-space
            vlspl:

        vlspl[2, ntypat, mqgrid_vl]
        Gives, on the radial grid, the local part of each type of psp.
        """
        return self.read_value("qgrid_vl"), self.read_value("vlspl")

    def read_projectors(self):
        """
        ffspl(ntypat, lnmax, 2, mqgrid_ff]
        Gives, on the radial grid, the different non-local projectors,
        in both the norm-conserving case, and the PAW case
        """
        # ekb(dimekb,ntypat*(1-usepaw))
        ekb = self.read_value("ekb")
        qgrid_ff = self.read_value("qgrid_ff")
        ffspl = self.read_value("ffspl")

        projs = self.ntypat * [None]
        for itypat in range(self.ntypat):
            projs_type = []
            ln_list = self.get_lnlist_for_type(itypat)
            for i, ln in enumerate(ln_list):
                p = VnlProjector(itypat, ln, ekb[itypat, i], qgrid_ff, ffspl[itypat, i, :, :])
                projs_type.append(p)

            projs[itypat] = projs_type

        return projs

    def get_lnlist_for_type(self, itypat):
        """Return a list of (l, n) indices for this atom type."""
        # indlmn(6,lmn_size,ntypat)=array giving l,m,n,lm,ln,s for i=lmn
        indlmn_type = self.indlmn[itypat, :, :]

        iln0 = 0; ln_list = []
        for ilmn in range(self.lmnmax):
            iln = indlmn_type[ilmn, 4]
            if iln > iln0:
              iln0 = iln
              l = indlmn_type[ilmn, 0]  # l
              n = indlmn_type[ilmn, 2]  # n
              ln_list.append((l, n))

        return ln_list


class VnlProjector(object):
    """Data and parameters associated to a non-local projector."""
    def __init__(self, itypat, ln, ekb, qmesh, data):
        """
        Args:
            itypat:
            ln: Tuple with l and n.
            ekb: KB energy in Hartree.
            qmesh: Mesh of q-points.
            data: numpy array [2, nqpt]
        """
        self.ln = ln
        self.l, self.n, self.ekb = ln[0], ln[1], ekb
        self.qmesh, self.data = qmesh, data

        assert len(self.qmesh) == len(self.values)
        assert len(self.qmesh) == len(self.der2)

    @property
    def values(self):
        """Values of the projector in q-space."""
        return self.data[0, :]

    @property
    def der2(self):
        """Second order derivative."""
        return self.data[1, :]

    @property
    def ecuts(self):
        """List of cutoff energies corresponding to self.qmesh."""
        return 2 * (np.pi * self.qmesh)**2

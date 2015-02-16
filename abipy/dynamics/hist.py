# coding: utf-8
"""DDB File."""
from __future__ import print_function, division, unicode_literals

#import os
import numpy as np

from monty.functools import lazy_property
from monty.collections import AttrDict
from pymatgen.core.units import EnergyArray, ArrayWithUnit
from pymatgen.util.plotting_utils import add_fig_kwargs, get_ax_fig_plt
from abipy.core.structure import Structure
from abipy.core.mixins import AbinitNcFile
from abipy.iotools import ETSF_Reader

import logging
logger = logging.getLogger(__name__)

__all__ = [
    "HistFile",
]


class HistFile(AbinitNcFile):
    """
    File with the history of a structural relaxation or molecular dynamics calculation.

    Usage example:
                                                                  
    .. code-block:: python
        
        with HistFile("foo_HIST") as hist:
            hist.plot_geo_hist()
    """
    @classmethod
    def from_file(cls, filepath):
        """Initialize the object from a Netcdf file"""
        return cls(filepath)

    def __init__(self, filepath):
        super(HistFile, self).__init__(filepath)

        self.reader = r = HistReader(filepath)
        print(self)

    def close(self):
        self.reader.close()

    @property
    def num_steps(self):
        """Number of iterations performed."""
        return self.reader.num_steps

    @lazy_property
    def structures(self):
        """List of structures at the different steps."""
        return self.reader.read_all_structures()

    @lazy_property
    def etotals(self):
        """numpy array with total energies at the different steps."""
        return self.reader.read_eterms().etotals

    def export(self, filename, visu=None):
        """
        Export the crystalline structure on file filename. 

        Args:
            filename: String specifying the file path and the file format.
                The format is defined by the file extension. filename="prefix.xsf", for example,
                will produce a file in XSF format. An *empty* prefix, e.g. ".xsf" makes the code use a temporary file.
            visu: `Visualizer` subclass. By default, this method returns the first available
                visualizer that supports the given file format. If visu is not None, an
                instance of visu is returned. See :class:`Visualizer` for the list of applications and formats supported.

        Returns: Instance of :class:`Visualizer`
        """
        print("Warning: work in progress")
        if "." not in filename:
            raise ValueError("Cannot detect extension in filename %s: " % filename)

        #import tempfile
        #_, tmpfile = tempfile.mkstemp(suffix='', prefix='.xsf', text=True)
        from abipy.iotools.xsf import xsf_write_structure
        with open(filename, "w") as fh:
            xsf_write_structure(fh, self.structures)

    @add_fig_kwargs
    def plot_lattice_hist(self, **kwargs):
        """
        Plot the evolution of the lattice parameters (abc parameters, angles and lattice volume)

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.

        Returns:
            `matplotlib` figure
        """
        import matplotlib.pyplot as plt
        fig, ax_list = plt.subplots(nrows=5, ncols=1, sharex=True, squeeze=False)
        ax_list = ax_list.ravel()
        ax0, ax1, ax2, ax3, ax4 = ax_list
        for ax in ax_list: ax.grid(True)

        steps = list(range(self.num_steps))

        # Lattice parameters.
        for i, label in enumerate(["a", "b", "c"]):
            ax0.plot(steps, [s.lattice.abc[i] for s in self.structures], marker="o", label=label)
        ax0.set_ylabel('Lattice lengths [A]')
        ax0.legend(loc='best', shadow=True)

        # Lattice Angles
        for i, label in enumerate(["alpha", "beta", "gamma"]):
            ax1.plot(steps, [s.lattice.angles[i] for s in self.structures], marker="o", label=label)
        ax1.set_ylabel('Lattice Angles [degree]')
        ax1.legend(loc='best', shadow=True)

        ax2.plot(steps, [s.lattice.volume for s in self.structures], marker="o") 
        ax2.set_ylabel('Lattice volume [A^3]')
        ax2.legend(loc='best', shadow=True)

        stress_cart_tensors, pressures = self.reader.read_cart_stress_tensors()
        axp = ax2.twinx()
        axp.plot(steps, pressures, marker="o", label="Pressure")
        axp.set_ylabel('Pressure [GPa]')
        axp.legend(loc='best', shadow=True)

        # Forces
        forces_hist = self.reader.read_cart_forces()
        fmin_steps, fmax_steps, fmean_steps, fstd_steps = [], [], [], []
        for step in range(self.num_steps):
            forces = forces_hist[step]
            fmods = np.sqrt([np.dot(force, force) for force in forces])
            fmean_steps.append(fmods.mean())
            fstd_steps.append(fmods.std())
            fmin_steps.append(fmods.min())
            fmax_steps.append(fmods.max())

        ax3.plot(steps, fmin_steps, marker="o", label="min |F|") 
        ax3.plot(steps, fmax_steps, marker="o", label="max |F|") 
        ax3.plot(steps, fmean_steps, marker="o", label="mean |F|") 
        ax3.plot(steps, fstd_steps, marker="o", label="std |F|") 
        ax3.set_ylabel('Force stats [eV/A]')
        ax3.legend(loc='best', shadow=True)

        # Total energy.
        ax4.plot(steps, self.etotals, marker="o") 
        ax4.set_ylabel('Total energy [eV]')
        ax4.set_xlabel('Step')

        return fig

    @add_fig_kwargs
    def plot_energy_hist(self, **kwargs):
        """
        Plot the evolution of the different contributions to the total energy.

        Args:
            ax: matplotlib :class:`Axes` or None if a new figure should be created.

        Returns:
            `matplotlib` figure
        """
        # TODO max force and pressure
        ax, fig, plt = get_ax_fig_plt(None)

        steps = list(range(self.num_steps))
        terms = self.reader.read_eterms()
        for key, values in terms.items():
            if np.all(values == 0.0): continue
            ax.plot(steps, values, marker="o", label=key)

        ax.set_xlabel('Step')
        ax.set_ylabel('Energies [eV]')
        ax.grid(True)
        ax.legend(loc='best', shadow=True)

        return fig


class HistReader(ETSF_Reader):
    """This object reads data from the HIST file."""

    @lazy_property
    def num_steps(self):
        """Number of iterations on file."""
        return self.read_dimvalue("time")

    @lazy_property
    def natom(self):
        """Number of atoms."""
        return self.read_dimvalue("natom")

    def read_all_structures(self):
        """Return the list of structures at the different iteration steps."""
        rprimd_list = self.read_value("rprimd")
        xred_list = self.read_value("xred")

        structures = []
        for step in range(self.num_steps):
            s = Structure.from_abivars(
                xred=xred_list[step],
                rprim=rprimd_list[step],
                acell=3 * [1.0],
                # FIXME ntypat, typat, znucl are missing!
                znucl=[14, 14],
                typat=[1, 1],
            )
            structures.append(s)

        return structures

    def read_eterms(self, unit="eV"):
        return AttrDict(
            etotals=EnergyArray(self.read_value("etotal"), "Ha").to(unit),
            kinetic_terms=EnergyArray(self.read_value("ekin"), "Ha").to(unit),
            entropies=EnergyArray(self.read_value("entropy"), "Ha").to(unit),
        )

    def read_cart_forces(self, unit="eV ang^-1"):
        """Read and return an array with the cartesian forces, shape (num_steps, natom, 3)"""
        return ArrayWithUnit(self.read_value("fcart"), "Ha bohr^-1").to(unit)

    def read_reduced_forces(self):
        """Read and return an array with the forces in reduced coordinates, shape (num_steps, natom, 3)"""
        return self.read_value("fred")

    def read_cart_stress_tensors(self):
        """
        Return the stress tensors (nstepx3x3 matrix) in cartesian coordinates (Hartree/Bohr^3)
        and the pressures in GPa.
        """
        # Abinit stores 6 unique components of this symmetric 3x3 tensor:
        # Given in order (1,1), (2,2), (3,3), (3,2), (3,1), (2,1).
        c = self.read_value("strten")
        tensors = np.empty((self.num_steps, 3, 3), dtype=np.float)

        for step in range(self.num_steps):
            for i in range(3): tensors[step, i,i] = c[step, i]
            for p, (i, j) in enumerate(((2,1), (2,0), (1,0))):
                tensors[step, i,j] = c[step, 3+p] 
                tensors[step, j,i] = c[step, 3+p]

        HaBohr3_GPa = 29421.033 # 1 Ha/Bohr^3, in GPa
        pressures = np.empty(self.num_steps)
        for step, tensor in enumerate(tensors):
            pressures[step] = - (HaBohr3_GPa/3) * tensor.trace()

        return tensors, pressures


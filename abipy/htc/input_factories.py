# coding: utf-8
"""Factory function for Abinit input files """
from __future__ import print_function, division, unicode_literals

#import os
import collections
#import copy
#import numpy as np

from collections import OrderedDict
from monty.string import is_string, list_strings
#from pymatgen.core.units import Energy
from pymatgen.io.abinitio.pseudos import PseudoTable, Pseudo
from pymatgen.io.abinitio.abiobjects import KSampling, Electrons, RelaxationMethod, Screening, SelfEnergy, ExcHamiltonian, HilbertTransform
from abipy.core.structure import Structure
from .input import AbiInput

import logging
logger = logging.getLogger(__file__)


# Name of the (default) tolerance used by the runlevels.
_runl2tolname = {
    "scf": 'tolvrs',
    "nscf": 'tolwfr',
    "dfpt": 'toldfe',        # ?
    "screening": 'toldfe',   # dummy
    "sigma": 'toldfe',       # dummy
    "bse": 'toldfe',         # ?
    "relax": 'tolrff',
}

# Tolerances for the different levels of accuracy.
T = collections.namedtuple('Tolerance', "low normal high")
_tolerances = {
    "toldfe": T(1.e-7,  1.e-8,  1.e-9),
    "tolvrs": T(1.e-7,  1.e-8,  1.e-9),
    "tolwfr": T(1.e-15, 1.e-17, 1.e-19),
    "tolrff": T(0.04,   0.02,   0.01)}
del T


def stopping_criterion(runlevel, accuracy):
    """Return the stopping criterion for this runlevel with the given accuracy."""
    tolname = _runl2tolname[runlevel]
    return {tolname: getattr(_tolerances[tolname], accuracy)}


def get_ecut_pawecutdg(ecut, pawecutdg, pseudos):
    return ecut, pawecutdg
    #if ecut is None: 
    #  ecut = max(p.hint for p in pseudos)
    #if pawecutdg is None and any(p.ispaw for p in pseudos):
    #    pawecutdg = max(p.hint for p in pseudos)


def ebands_input(structure, pseudos, scf_kppa, nscf_nband, ndivsm, 
                 ecut=None, pawecutdg=None, accuracy="normal", spin_mode="polarized",
                 smearing="fermi_dirac:0.1 eV", charge=0.0, scf_algorithm=None, dos_kppa=None):
    """
    Returns a :class:`AbiInput` for band structure calculations.

    Args:
        structure: :class:`Structure` object.
        pseudos: List of `Pseudo` objects.
        scf_kppa: Defines the sampling used for the SCF run.
        nscf_nband: Number of bands included in the NSCF run.
        ndivsm: Number of divisions used to sample the smallest segment of the k-path.
        ecut: cutoff energy in Ha (if None, ecut is initialized from the pseudos according to accuracy)
        pawecutdg: cutoff energy in Ha for PAW double-grid (if None, pawecutdg is initialized from the pseudos according to accuracy)
        accuracy: Accuracy of the calculation.
        spin_mode: Spin polarization.
        smearing: Smearing technique.
        charge: Electronic charge added to the unit cell.
        scf_algorithm: Algorithm used for solving of the SCF cycle.
        dos_kppa: Defines the k-point sampling used for the computation of the DOS
            (None if DOS is not wanted).
    """
    # TODO: To be discussed: 
    #    1) extra_abivars is more similar to a hack. The factory functions are designed for
    #       HPC hence we cannot allow the user to inject something we cannot control easily
    #       Shall we remove it?
    #    2) scf_nband and nscf_band should be computed from the pseudos, the structure
    #       and some approximation for the band dispersion.
    #       SCF fails if nband is too small or has problems if we don't have enough partially
    #       occupied states in metals (can write EventHandler but it would be nice if we could
    #       fix this problem in advance.
    #   
    structure = Structure.as_structure(structure)
    pseudos = PseudoTable.as_table(pseudos).get_pseudos_for_structure(structure)

    inp = AbiInput(pseudos, ndtset=2 if dos_kppa is None else 3)
    inp.set_structure(structure)

    # Set the cutoff energy
    ecut, pawecutdg = get_ecut_pawecutdg(ecut, pawecutdg, pseudos)
    inp.set_vars(ecut=ecut, pawecutdg=pawecutdg)

    # SCF calculation.
    scf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)
    scf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm=scf_algorithm, 
                              charge=charge) #, nband=None, fband=None)

    inp[1].set_vars(scf_ksampling.to_abivars())
    inp[1].set_vars(scf_electrons.to_abivars())
    inp[1].set_vars(stopping_criterion("scf", accuracy))

    # Band structure calculation.
    nscf_ksampling = KSampling.path_from_structure(ndivsm, structure)
    nscf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm={"iscf": -2},
                               charge=charge, nband=nscf_nband) # fband=None)
    #nscf_strategy = NscfStrategy(scf_strategy, nscf_ksampling, nscf_nband, **extra_abivars)

    inp[2].set_vars(nscf_ksampling.to_abivars())
    inp[2].set_vars(nscf_electrons.to_abivars())
    inp[2].set_vars(stopping_criterion("nscf", accuracy))

    # DOS calculation.
    if dos_kppa is not None:
        #dos_strategy = NscfStrategy(scf_strategy, dos_ksampling, nscf_nband, nscf_solver=None, **extra_abivars)
        dos_ksampling = KSampling.automatic_density(structure, dos_kppa, chksymbreak=0)
        #dos_ksampling = KSampling.monkhorst(dos_ngkpt, shiftk=dos_shiftk, chksymbreak=0)
        dos_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm={"iscf": -2},
                                  charge=charge, nband=nscf_nband) 

        inp[3].set_vars(dos_ksampling.to_abivars())
        inp[3].set_vars(dos_electrons.to_abivars())
        inp[3].set_vars(stopping_criterion("nscf", accuracy))

    return inp


def ion_ioncell_relax_input(structure, pseudos, kppa, nband,
                            ecut=None, pawecutdg=None, accuracy="normal", spin_mode="polarized",
                            smearing="fermi_dirac:0.1 eV", charge=0.0, scf_algorithm=None):
    """
    Returns a :class:`AbiInput` for band structure calculations.

    Args:
        structure: :class:`Structure` object.
        pseudos: List of `Pseudo` objects.
        kppa: Defines the sampling used for the Brillouin zone.
        nband: Number of bands included in the SCF run.
        accuracy: Accuracy of the calculation.
        spin_mode: Spin polarization.
        smearing: Smearing technique.
        charge: Electronic charge added to the unit cell.
        scf_algorithm: Algorithm used for solving of the SCF cycle.
    """
    structure = Structure.as_structure(structure)
    pseudos = PseudoTable.as_table(pseudos).get_pseudos_for_structure(structure)

    inp = AbiInput(pseudos, ndtset=2)
    inp.set_structure(structure)

    # Set the cutoff energy
    ecut, pawecutdg = get_ecut_pawecutdg(ecut, pawecutdg, pseudos)
    inp.set_vars(ecut=ecut, pawecutdg=pawecutdg)

    ksampling = KSampling.automatic_density(structure, kppa, chksymbreak=0)
    electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm=scf_algorithm, 
                          charge=charge) #, nband=None, fband=None)

    ion_relax = RelaxationMethod.atoms_only(atoms_constraints=None)
    ioncell_relax = RelaxationMethod.atoms_and_cell(atoms_constraints=None)

    inp.set_vars(electrons.to_abivars())
    inp.set_vars(ksampling.to_abivars())

    inp[1].set_vars(ion_relax.to_abivars())
    # Stopping criterion is already in RelaxationMethod
    # TODO: Use similar approach for Scf
    #inp[1].set_vars(stopping_criterion("relax", accuracy))

    inp[2].set_vars(ioncell_relax.to_abivars())

    return inp


def g0w0_with_ppmodel_input(structure, pseudos, scf_kppa, nscf_nband, ecuteps, ecutsigx,
                            ecut=None, pawecutdg=None,
                            accuracy="normal", spin_mode="polarized", smearing="fermi_dirac:0.1 eV",
                            ppmodel="godby", charge=0.0, scf_algorithm=None, inclvkb=2, scr_nband=None,
                            sigma_nband=None, gw_qprange=1):
    """
    Returns a :class:`AbiInput` object that performs G0W0 calculations with the plasmon pole approximation.

    Args:
        structure: Pymatgen structure.
        pseudos: List of `Pseudo` objects.
        scf_kppa: Defines the sampling used for the SCF run.
        nscf_nband: Number of bands included in the NSCF run.
        ecuteps: Cutoff energy [Ha] for the screening matrix.
        ecutsigx: Cutoff energy [Ha] for the exchange part of the self-energy.
        ecut: cutoff energy in Ha (if None, ecut is initialized from the pseudos according to accuracy)
        pawecutdg: cutoff energy in Ha for PAW double-grid (if None, pawecutdg is initialized from the pseudos according to accuracy)
        accuracy: Accuracy of the calculation.
        spin_mode: Spin polarization.
        smearing: Smearing technique.
        ppmodel: Plasmonpole technique.
        charge: Electronic charge added to the unit cell.
        scf_algorithm: Algorithm used for solving of the SCF cycle.
        inclvkb: Treatment of the dipole matrix elements (see abinit variable).
        scr_nband: Number of bands used to compute the screening (default is nscf_nband)
        sigma_nband: Number of bands used to compute the self-energy (default is nscf_nband)
        gw_qprange: Option for the automatic selection of k-points and bands for GW corrections.
            See Abinit docs for more detail. The default value makes the code compute the
            QP energies for all the point in the IBZ and one band above and one band below the Fermi level.
    """
    structure = Structure.as_structure(structure)
    pseudos = PseudoTable.as_table(pseudos).get_pseudos_for_structure(structure)

    inp = AbiInput(pseudos, ndtset=4)
    inp.set_structure(structure)

    # Set the cutoff energy
    ecut, pawecutdg = get_ecut_pawecutdg(ecut, pawecutdg, pseudos)
    inp.set_vars(ecut=ecut, pawecutdg=pawecutdg)

    scf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)

    scf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm=scf_algorithm, 
                              charge=charge) #, nband=None, fband=None)

    #scf_strategy = ScfStrategy(structure, pseudos, scf_ksampling,
    #                           accuracy=accuracy, spin_mode=spin_mode,
    #                           smearing=smearing, charge=charge,
    #                           scf_algorithm=scf_algorithm)

    inp[1].set_vars(scf_ksampling.to_abivars())
    inp[1].set_vars(scf_electrons.to_abivars())
    inp[1].set_vars(stopping_criterion("scf", accuracy))

    nscf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)
    nscf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm={"iscf": -2},
                               charge=charge, nband=nscf_nband) # fband=None)
    #nscf_strategy = NscfStrategy(scf_strategy, nscf_ksampling, nscf_nband)

    inp[2].set_vars(nscf_ksampling.to_abivars())
    inp[2].set_vars(nscf_electrons.to_abivars())
    inp[2].set_vars(stopping_criterion("nscf", accuracy))
    # nbdbuf

    # Screening.
    if scr_nband is None: scr_nband = nscf_nband
    screening = Screening(ecuteps, scr_nband, w_type="RPA", sc_mode="one_shot",
                          hilbert=None, ecutwfn=None, inclvkb=inclvkb)
    inp[3].set_vars(screening.to_abivars())
    #scr_strategy = ScreeningStrategy(scf_strategy, nscf_strategy, screening)

    # Sigma.
    if sigma_nband is None: sigma_nband = nscf_nband
    self_energy = SelfEnergy("gw", "one_shot", sigma_nband, ecutsigx, screening,
                             gw_qprange=gw_qprange, ppmodel=ppmodel)
    inp[4].set_vars(self_energy.to_abivars())
    #sigma_strategy = SelfEnergyStrategy(scf_strategy, nscf_strategy, scr_strategy, self_energy)

    # TODO: Cannot use istwfk != 1.
    inp.set_vars(istwfk="*1")

    return inp

#TODO
#def g0w0_extended_work(structure, pseudos, scf_kppa, nscf_nband, ecuteps, ecutsigx, scf_nband, accuracy="normal",


def bse_with_mdf_input(structure, pseudos, scf_kppa, nscf_nband, nscf_ngkpt, nscf_shiftk, 
                       ecuteps, bs_loband, bs_nband, soenergy, mdf_epsinf, 
                       ecut=None, pawecutdg=None, 
                       exc_type="TDA", bs_algo="haydock", accuracy="normal", spin_mode="polarized", 
                       smearing="fermi_dirac:0.1 eV", charge=0.0, scf_algorithm=None):
    """
    Returns a :class:`AbiInput` object that performs a GS + NSCF + Bethe-Salpeter calculation.
    The self-energy corrections are approximated with the scissors operator.
    The screening in modeled with the model dielectric function.

    Args:
        structure: :class:`Structure` object.
        pseudos: List of `Pseudo` objects.
        scf_kppa: Defines the sampling used for the SCF run.
        nscf_nband: Number of bands included in the NSCF run.
        nscf_ngkpt: Divisions of the k-mesh used for the NSCF and the BSE run.
        nscf_shiftk: Shifts used for the NSCF and the BSE run.
        ecuteps: Cutoff energy [Ha] for the screening matrix.
        bs_loband: Index of the first occupied band included the e-h basis set
            (ABINIT convention i.e. first band starts at 1).
            Can be scalar or array of shape (nsppol,)
        bs_nband: Highest band idex used for the construction of the e-h basis set.
        soenergy: Scissor energy in Hartree.
        mdf_epsinf: Value of the macroscopic dielectric function used in expression for the model dielectric function.
        ecut: cutoff energy in Ha (if None, ecut is initialized from the pseudos according to accuracy)
        pawecutdg: cutoff energy in Ha for PAW double-grid (if None, pawecutdg is initialized from the pseudos according to accuracy)
        exc_type: Approximation used for the BSE Hamiltonian (Tamm-Dancoff or coupling).
        bs_algo: Algorith for the computatio of the macroscopic dielectric function.
        accuracy: Accuracy of the calculation.
        spin_mode: Spin polarization.
        smearing: Smearing technique.
        charge: Electronic charge added to the unit cell.
        scf_algorithm: Algorithm used for solving the SCF cycle.
    """
    structure = Structure.as_structure(structure)
    pseudos = PseudoTable.as_table(pseudos).get_pseudos_for_structure(structure)

    inp = AbiInput(pseudos, ndtset=3)
    inp.set_structure(structure)

    # Set the cutoff energy
    ecut, pawecutdg = get_ecut_pawecutdg(ecut, pawecutdg, pseudos)
    inp.set_vars(ecut=ecut, pawecutdg=pawecutdg)

    # Ground-state 
    scf_ksampling = KSampling.automatic_density(structure, scf_kppa, chksymbreak=0)

    scf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm=scf_algorithm, 
                              charge=charge) #, nband=None, fband=None)

    inp[1].set_vars(scf_ksampling.to_abivars())
    inp[1].set_vars(scf_electrons.to_abivars())
    inp[1].set_vars(stopping_criterion("scf", accuracy))

    # NSCF calculation with the randomly-shifted k-mesh.
    nscf_ksampling = KSampling.monkhorst(nscf_ngkpt, shiftk=nscf_shiftk, chksymbreak=0)

    nscf_electrons = Electrons(spin_mode=spin_mode, smearing=smearing, algorithm={"iscf": -2},
                               charge=charge, nband=nscf_nband) # fband=None)

    inp[2].set_vars(nscf_ksampling.to_abivars())
    inp[2].set_vars(nscf_electrons.to_abivars())
    inp[2].set_vars(stopping_criterion("nscf", accuracy))

    # BSE calculation.
    exc_ham = ExcHamiltonian(bs_loband, bs_nband, soenergy, coulomb_mode="model_df", ecuteps=ecuteps, 
                             spin_mode=spin_mode, mdf_epsinf=mdf_epsinf, exc_type=exc_type, algo=bs_algo,
                             bs_freq_mesh=None, with_lf=True, zcut=None)

    inp[3].set_vars(nscf_ksampling.to_abivars())
    inp[3].set_vars(nscf_electrons.to_abivars())
    inp[3].set_vars(exc_ham.to_abivars())
    #inp[3].set_vars(stopping_criterion("nscf", accuracy))

    # TODO: Cannot use istwfk != 1.
    inp.set_vars(istwfk="*1")

    return inp

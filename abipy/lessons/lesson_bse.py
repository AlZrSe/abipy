#!/usr/bin/env python
from __future__ import division, print_function

import os
import numpy as np
import abipy.abilab as abilab 
import abipy.data as abidata


def make_scf_nscf_bse_inputs(ngkpt=(6, 6, 6), ecut=6, ecuteps=3, 
                             mdf_epsinf=12.0, soenergy="0.8 eV"):
    """
    Build and returns three `AbinitInput` object to perform a 
    GS-SCF + GS-NSCF + BSE calculation. with the model dielectric function.

    Args:
        ngkpt: Three integers giving the number of divisions for the k-mesh.
        ecut: Cutoff energy for the wavefunctions.
        ecuteps: Cutoff energy for the screened interation W_{GG'}.
        mdf_epsinf: Static limit of the macroscopic dielectric functions. 
            Used to build the model dielectric function.
        soenergy: Scissors operator energy (used to open the initial KS gap).
    """
    multi = abilab.MultiDataset(structure=abidata.structure_from_ucell("Si"),
                                pseudos=abidata.pseudos("14si.pspnc"), ndtset=3)

    # Variables common to the three datasets.
    multi.set_vars(
        ecut=ecut, 
        nband=8,
        istwfk="*1",
        diemac=12.0,
    )

    # SCF run to get the density.
    multi[0].set_vars(tolvrs=1e-8)
    multi[0].set_kmesh(ngkpt=ngkpt, shiftk=(0, 0, 0))

    # NSCF run on a randomly shifted k-mesh (improve the converge of optical properties)
    multi[1].set_vars(
        iscf=-2,
        nband=15,
        tolwfr=1e-8,
        chksymbreak=0,                # Skip the check on the k-mesh.
    )

    # This shift breaks the symmetry of the k-mesh.
    multi[1].set_kmesh(ngkpt=ngkpt, shiftk=(0.11, 0.21, 0.31))

    # BSE run with Haydock iterative method (only resonant + W + v)
    multi[2].set_vars(
        optdriver=99,                 # BS calculation
        chksymbreak=0,                # To skip the check on the k-mesh.
        bs_calctype=1,                # L0 is contstructed with KS orbitals and energies.
        soenergy=soenergy,            # Scissors operator used to correct the KS band structure.
        bs_exchange_term=1,           # Exchange term included.
        bs_coulomb_term=21,           # Coulomb term with model dielectric function.
        mdf_epsinf=mdf_epsinf,        # Parameter for the model dielectric function.
        bs_coupling=0,                # Tamm-Dancoff approximation.
        bs_loband=2,                  # Lowest band included in the calculation
        nband=6,                      # Highest band included in the calculation
        bs_freq_mesh="0 6 0.02 eV",   # Frequency mesh for the dielectric function
        bs_algorithm=2,               # Use Haydock method.
        zcut="0.15 eV",               # Complex shift to avoid divergences in the continued fraction.
        ecutwfn=ecut,                 # Cutoff for the wavefunction.
        ecuteps=ecuteps,              # Cutoff for W and /bare v.
        inclvkb=2,                    # The commutator for the optical limit is correctly evaluated.
    )

    # Same shift as the one used in the previous dataset.
    multi[2].set_kmesh(ngkpt=ngkpt, shiftk=(0.11, 0.21, 0.31))

    scf_input, nscf_input, bse_input = multi.split_datasets()
    return scf_input, nscf_input, bse_input


#def eh_convergence_study():
#    """
#    """
#    scf_input, nscf_input, bse_input = make_inputs()
#
#    flow = abilab.Flow(workdir="flow_bse_ecuteps")
#    work = abilab.BseMdfWork(scf_input, nscf_input, bse_input)
#
#    flow.register_work(work)
#    flow.make_scheduler().start()
#
#    import matplotlib.pyplot as plt
#    import pandas as pd
#
#    #with abilab.abirobot(flow, "MDF") as robot:
#        #frame = robot.get_dataframe()
#        #print(frame)
#        #plotter = robot.get_mdf_plotter()
#        #plotter.plot()
#        #robot.plot_conv_mdf(hue="broad")
#
#        #grouped = frame.groupby("broad")
#        #fig, ax_list = plt.subplots(nrows=len(grouped), ncols=1, sharex=True, sharey=True, squeeze=True)
#
#        #for i, (zcut, group) in enumerate(grouped):
#        #    print(group)
#        #    mdfs = group["exc_mdf"] 
#        #    ax = ax_list[i]
#        #    ax.set_title("zcut %s" % zcut)
#        #    for mdf in mdfs:
#        #        mdf.plot_ax(ax)
#        #plt.show()

#if __name__ == "__main__":
#    eh_convergence_study()

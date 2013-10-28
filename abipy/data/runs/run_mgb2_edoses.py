#!/usr/bin/env python
"""
This script computes the band structure and the electron DOS of MgB2
with different k-point samplings.
"""
from __future__ import division, print_function

import os
import abipy.data as data  
import abipy.abilab as abilab

from abipy.data.runs import Tester, enable_logging
from abipy.core.testing import AbipyTest


def make_scf_nscf_inputs(structure, pseudos):

    inp = abilab.AbiInput(pseudos=pseudos, ndtset=5)
    inp.set_structure(structure)

    # Global variables
    global_vars = dict(ecut=10,
                       nband=11,
                       timopt=-1,
                       occopt=4,    # Marzari smearing
                       tsmear=0.03,
                    )

    inp.set_variables(**global_vars)

    # Dataset 1 (GS run)
    inp[1].set_kmesh(ngkpt=[8,8,8], 
                    shiftk=structure.calc_shiftk(),
                   )

    inp[1].set_variables(tolvrs=1e-6)

    # Dataset 2 (NSCF Band Structure)
    inp[2].set_kpath(ndivsm=6)
    inp[2].set_variables(tolwfr=1e-12)

    # Dos calculations with increasing k-point sampling.
    for i, nksmall in enumerate([10, 14, 18]):
        inp[i+3].set_variables(
            iscf=-3,   # NSCF calculation
            ngkpt=structure.calc_ngkpt(nksmall),      
            shiftk=[0.0, 0.0, 0.0],
            tolwfr=1.0e-10,
        )
    
    # return GS, NSCF (band structure), DOSes input.
    return  inp.split_datasets()


def build_bands_flow(workdir):
    pseudos = data.pseudos("12mg.pspnc", "05b.soft_tm")
    structure = data.structure_from_ucell("MgB2")

    nval = structure.calc_nvalence(pseudos)
    print(nval)

    inputs = make_scf_nscf_inputs(structure, pseudos)
    scf_input, nscf_input, dos_inputs = inputs[0], inputs[1], inputs[2:]
    print(scf_input.pseudos)

    manager = abilab.TaskManager.from_user_config()
                                                               
    flow = abilab.bandstructure_flow(workdir, manager, scf_input, nscf_input, dos_inputs=dos_inputs)

    return flow.allocate()

@enable_logging
def main():
    tester = Tester()
    flow = build_bands_flow(tester.workdir)
    return flow.build_and_pickle_dump()


if __name__ == "__main__":
    import sys
    sys.exit(main())

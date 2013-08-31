#!/usr/bin/env python
from __future__ import division, print_function

import os
import abipy.data as data  

from pymatgen.io.abinitio.abiobjects import AbiStructure
from pymatgen.io.abinitio.task import RunMode
from pymatgen.io.abinitio.calculations import bandstructure
from abipy.data.runs import RunManager


def main():
    structure = AbiStructure.asabistructure(data.cif_file("si.cif"))
    runmode = RunMode.sequential()

    scf_kppa = 40
    nscf_nband = 6
    ndivsm = 5
    #dos_ngkpt = [4,4,4]
    #dos_shiftk = [0.1, 0.2, 0.3]

    extra_abivars = dict(
        ecut=6, 
        timopt=-1,
        accesswff=3, 
        istwfk="*1",
    )

    manager = RunManager()

    work = bandstructure(manager.workdir, runmode, structure, data.pseudos("14si.pspnc"),
                         scf_kppa, nscf_nband, ndivsm, 
                         spin_mode="unpolarized", smearing=None, **extra_abivars)

    #dos_kppa = 10
    #bands = bandstructure("hello_dos", runmode, structure, pseudos, scf_kppa, nscf_nband,
    #                      ndivsm, accuracy="normal", spin_mode="polarized",
    #                      smearing="fermi_dirac:0.1 eV", charge=0.0, scf_solver=None,
    #                      dos_kppa=dos_kppa)

    manager.set_work_and_run(work)

    if manager.retcode != 0:
        return manager.retcode

    # Remove all files except those matching these regular expression.
    work[0].rename("out_WFK_0-etsf.nc", "si_scf_WFK-etsf.nc")
    work[0].rename("out_DEN-etsf.nc", "si_DEN-etsf.nc")
    work[0].rename("out_GSR.nc", "si_scf_GSR.nc")

    work[1].rename("out_GSR.nc", "si_nscf_GSR.nc")

    work.rmtree(exclude_wildcard="*.abin|*.about|*_WFK*|*_GSR.nc|*DEN-etsf.nc")

    manager.finalize()

    return manager.retcode 


if __name__ == "__main__":
    import sys
    sys.exit(main())

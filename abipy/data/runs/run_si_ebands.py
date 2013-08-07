#!/usr/bin/env python
from __future__ import division, print_function

import sys
import abipy.data as data  

from pymatgen.io.abinitio.abiobjects import AbiStructure
from pymatgen.io.abinitio.task import RunMode
from pymatgen.io.abinitio.pseudos import PseudoTable
from pymatgen.io.abinitio.launcher import SimpleResourceManager
from pymatgen.io.abinitio.calculations import bandstructure

def main():
    structure = AbiStructure.asabistructure(data.cif_file("si.cif"))

    pseudos = PseudoTable(data.pseudos("14si.pspnc"))
    runmode = RunMode.sequential()

    kppa = scf_kppa = 40
    nscf_nband = 6
    ndivsm = 5
    dos_ngkpt = [4,4,4]
    dos_shiftk = [0.1, 0.2, 0.3]
    max_ncpus = 1

    extra_abivars = dict(
        ecut=12, 
        accesswff=3, 
        istwfk="*1",
    )

    work = bandstructure("silicon_gs+nscf", runmode, structure, pseudos, scf_kppa, nscf_nband, ndivsm, 
                         spin_mode="unpolarized", smearing=None, **extra_abivars)

    retcodes = SimpleResourceManager(work, max_ncpus, sleep_time=5).run()

    work[0].rename("out_WFK_0-etsf.nc", "si_scf_WFK-etsf.nc")
    work[1].rename("out_WFK_0-etsf.nc", "si_nscf_WFK-etsf.nc")

    #work.rmtree()

    return max(retcodes)

    #dos_kppa = 10
    #bands = bandstructure("hello_dos", runmode, structure, pseudos, scf_kppa, nscf_nband,
    #                      ndivsm, accuracy="normal", spin_mode="polarized",
    #                      smearing="fermi_dirac:0.1 eV", charge=0.0, scf_solver=None,
    #                      dos_kppa=dos_kppa)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
from __future__ import division, print_function

import os
import abipy.data as data  
import abipy.abilab as abilab

from abipy.data.runs import Tester, decorate_main
from pseudo_dojo.dojo.deltaworks import DeltaFactory


def delta_flow():
    # Path of the pseudopotential to test.
    pseudo = data.pseudos("14si.pspnc")[0]

    # Manager used to submit the jobs.
    manager = abilab.TaskManager.simple_mpi(mpi_ncpus=2)

    # Use this for manneback and edit the YAML file according to your platform
    #manager = abilab.TaskManager.from_file("taskmanager.yaml") 

    # Initialize the flow.
    flow = abilab.AbinitFlow(workdir="DELTAFACTOR", manager=manager)

    # Build the wrorkflow for the computation of the deltafactor.
    factory = DeltaFactory()
    work = factory.work_for_pseudo(pseudo, accuracy="normal", kppa=50, 
                                   ecut=8, toldfe=1.e-8, smearing="fermi_dirac:0.0005")

    # Register the input.
    flow.register_work(work)
    return flow.allocate()


@decorate_main
def main():
    flow = delta_flow()

    # Don't know why protocol=-1 does not work here.
    flow.build_and_pickle_dump(protocol=0)

if __name__ == "__main__":
    import sys
    sys.exit(main())

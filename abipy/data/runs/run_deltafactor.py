#!/usr/bin/env python
"""Compute the deltafactor for a given pseudopotential."""
from __future__ import division, print_function

import os
import sys
import abipy.data as data  
import abipy.abilab as abilab

from abipy.data.runs import enable_logging, AbipyTest, MixinTest
from pseudo_dojo.dojo.deltaworks import DeltaFactory


class DeltaFactorFlowTest(AbipyTest, MixinTest):
    """
    Unit test for the flow defined in this module.  
    Users who just want to learn how to use this flow can ignore this section.
    """
    def setUp(self):
        super(DeltaFactorFlowTest, self).setUp()
        self.init_dirs()
        self.flow = delta_flow(workdir=self.workdir)


def delta_flow(workdir="tmp_deltafactor"):
    # Path of the pseudopotential to test.
    #pseudo = data.pseudo("14si.pspnc")
    pseudo = data.pseudo("Si.GGA_PBE-JTH-paw.xml")

    # Manager used to submit the jobs.
    manager = abilab.TaskManager.from_user_config()

    # Initialize the flow.
    # FIXME  Abistructure is not pickleable with protocol -1
    flow = abilab.AbinitFlow(workdir=workdir, manager=manager, pickle_protocol=0)

    # Build the workflow for the computation of the deltafactor.
    # The calculation is done with the parameters and the cif files
    # used in the original paper. We only have to specify 
    # the cutoff energy ecut (Ha) for the pseudopotential.
    # The workflow will produce a pdf file with the equation of state 
    # and a file deltafactor.txt with the final results in the 
    # outdir directory DELTAFACTOR/work_0/outdir.
    factory = DeltaFactory()

    kppa = 6750  # Use this to have the official k-point sampling
    kppa = 50    # this value is for testing purpose.

    #extra = {}

    ecut = 8
    pawecutdg = ecut * 2 #if pseudo.ispaw else None

    work = factory.work_for_pseudo(pseudo, accuracy="normal", kppa=kppa, 
                                   ecut=ecut, pawecutdg=pawecutdg,
                                   toldfe=1.e-8, smearing="fermi_dirac:0.0005")

    # Register the workflow.
    flow.register_work(work)

    return flow.allocate()


@enable_logging
def main():
    flow = delta_flow()
    return flow.build_and_pickle_dump()

if __name__ == "__main__":
    sys.exit(main())

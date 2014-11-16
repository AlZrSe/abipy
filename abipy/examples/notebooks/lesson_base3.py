#!/usr/bin/env python
from __future__ import division, print_function

import abipy.abilab as abilab 
import abipy.data as abidata


def ngkpt_flow():
    ngkpt_list = [(2, 2, 2), (4, 4, 4), (6, 6, 6), (8, 8, 8)]

    inp = abilab.AbiInput(pseudos=abidata.pseudos("14si.pspnc"), ndtset=len(ngkpt_list))
    structure = inp.set_structure_from_file(abidata.cif_file("si.cif"))

    # Global variables
    inp.set_variables(ecut=10, tolvrs=1e-9)

    for i, ngkpt in enumerate(ngkpt_list):
        inp[i+1].set_kmesh(ngkpt=ngkpt, shiftk=[0,0,0])

    work = abilab.Workflow()
    for dataset in inp.split_datasets():
        work.register_scf_task(dataset)

    flow = abilab.AbinitFlow(workdir="flow_ngkpt")
    flow.register_work(work)
    flow.allocate()
    flow.build()

    #flow.rapidfire()
    flow.make_scheduler().start()
    flow.show_status()

    table = abilab.PrettyTable(["nkibz", "etotal"])

    for task in flow[0]:
        gsr = task.read_gsr()
        table.add_row([len(gsr.kpoints), gsr.energy])

    print(table)
    #table.plot("nkibz", "etotal", title="etotal vs nkibz")

def relax_flow():
    # Structural relaxation
    ngkpt_list = [(2, 2, 2), (4, 4, 4)]
    inp = abilab.AbiInput(pseudos=abidata.pseudos("14si.pspnc"), ndtset=len(ngkpt_list))
    structure = inp.set_structure_from_file(abidata.cif_file("si.cif"))

    # Global variables
    inp.set_variables(
        ecut=10,
        tolvrs=1e-9,
        optcell=1,
        ionmov=3,
        ntime=10,
        dilatmx=1.05,
        ecutsm=0.5,
    )

    for i, ngkpt in enumerate(ngkpt_list):
        inp[i+1].set_kmesh(ngkpt=ngkpt, shiftk=[0,0,0])

    work = abilab.Workflow()
    for dataset in inp.split_datasets():
        #print(dataset)
        work.register_relax_task(dataset)

    flow = abilab.AbinitFlow(workdir="flow_relax"))
    flow.register_work(work)
    flow.allocate()
    flow.build()

    flow.make_scheduler().start()
    flow.show_status()

    table = PrettyTable(["nkibz", "a [Ang]", "angles", "volume [Ang^3]"])

    for task in flow[0]:
        with task.read_gsr() as gsr:
            lattice = gsr.structure.lattice
            table.add_row([len(gsr.kpoints), lattice.abc[0], lattice.angles[0], lattice.volume])

    print(table)
    #table.plot()

def bands_flow():
    inp = abilab.AbiInput(pseudos=abidata.pseudos("14si.pspnc"), ndtset=2)
    structure = inp.set_structure_from_file(abidata.cif_file("si.cif"))

    # Global variables
    inp.ecut = 10

    # Dataset 1
    inp[1].set_variables(tolvrs=1e-9)
    inp[1].set_kmesh(ngkpt=[4,4,4], shiftk=[0,0,0])

    # Dataset 2
    inp[2].set_variables(tolwfr=1e-15)
    inp[2].set_kpath(ndivsm=5)

    scf_input, nscf_input = inp.split_datasets()

    flow = abilab.bandstructure_flow(workdir="flow_bands", scf_input=scf_input, nscf_input=nscf_input)
    flow.build_and_pickle_dump()

    flow.make_scheduler().start()
    flow.show_status()
    
    nscf_task = flow[0][1]
    with nscf_task.read_gsr() as gsr:
        gsr.ebands.plot()


if __name__ == "__main__":
    #ngkpt_flow()
    #relax_flow()
    bands_flow()

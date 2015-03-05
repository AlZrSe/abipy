from __future__ import division, print_function, unicode_literals

import sys
import os
import abipy.data as abidata  
import abipy.abilab as abilab


def itest_tolsymerror_handler(fwp):
    """
    Test the handler of TolSymError. The test triggers:
    
        --- !TolSymError
        message: |
            Could not find the point group
        src_file: symptgroup.F90
        src_line: 236
        ...
    
    at the level of the symmetry finder and autoparal fails 
    because it cannot find the parallel configurations.
    """
    inp = abilab.AbiInput(pseudos=abidata.pseudos("14si.pspnc"), ndtset=1)

    inp.set_vars(
         acell=(1.0, 1.0, 1.0),
         xred = [
            1.0001907690, 1.0040151117, 0.0099335191,
            0.2501907744, 0.2540150788, 0.2599335332],
         ntime=5,
         tolrff=0.02,
         typat=(1, 1),
         shiftk=[0, 0, 0],
         ntypat=1,
         ngkpt=(4, 4, 4),
         znucl=14,
         chksymbreak=0,
         rprim = [
           -6.2733366562, 0.0000000000, -3.6219126071,
           -6.2733366562, 0.0000000000,  3.6219126071,
           -4.1822244376, 5.9145585205,  0.0000000000],
         ecut=4,
         natom=2,
         tolmxf=5e-05,
         nshiftk=1,
        )

    flow = abilab.Flow(workdir=fwp.workdir, manager=fwp.manager)
    #flow.register_task(inp, task_class=abilab.ScfTask)
    flow.register_task(inp, task_class=abilab.RelaxTask)

    flow.allocate()
    flow.make_scheduler().start()

    flow.show_status()
    assert flow.all_ok

    task = flow[0][0]
    assert len(task.corrections) == 1
    assert task.corrections[0]["event"]["@class"] == "TolSymError"

    #assert task.corrections.count("TolSymError") == 1
    #assert 0


def itest_dilatmxerror_handler(fwp):
    """Test the handler of DilatmxError. The test triggers:

        --- !DilatmxError
        message: |
            Dilatmx has been exceeded too many times (4)
            Restart your calculation from larger lattice vectors and/or a larger dilatmx
        src_file: mover.F90
        src_line: 840
        ...
   
    in variable cell structural optimizations.
    """
    structure = abilab.Structure.from_file(abidata.cif_file("si.cif"))
    structure.scale_lattice(structure.volume * 0.6)

    # Perturb the structure (random perturbation of 0.1 Angstrom)
    #structure.perturb(distance=0.1)

    global_vars = dict(
        ecut=4,  
        ngkpt=[4,4,4], 
        shiftk=[0,0,0],
        nshiftk=1,
        chksymbreak=0,
        paral_kgb=1, 
    )

    inp = abilab.AbiInput(pseudos=abidata.pseudos("14si.pspnc"), ndtset=1)
    inp.set_structure(structure)

    # Global variables
    inp.set_vars(**global_vars)

    # Dataset 2 (Atom + Cell Relaxation)
    inp[1].set_vars(
        optcell=1,
        ionmov=2,
        ecutsm=0.5,
        dilatmx=1.01,
        tolrff=0.02,
        tolmxf=5.0e-5,
        strfact=100,
        ntime=50,
        #ntime=5, To test the restart
        )

    # Create the flow
    flow = abilab.Flow(fwp.workdir, manager=fwp.manager)
    flow.register_task(inp, task_class=abilab.RelaxTask)

    flow.allocate()
    flow.make_scheduler().start()

    flow.show_status()
    assert flow.all_ok

    task = flow[0][0]
    assert len(task.corrections) == 2
    for i in range(task.num_corrections):
        assert task.corrections[i]["event"]["@class"] == "DilatmxError"
    #assert 0

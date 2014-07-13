"""Integration tests for pseudodojo."""
from __future__ import print_function, division

import pytest
import abipy.data as abidata
import abipy.abilab as abilab

from abipy.core.testing import has_abinit

has_pseudodojo = True
try:
    import pseudo_dojo
except ImportError:
    has_pseudodojo = False

# Tests in this module require abinit >= 7.9.0 and pseudodojo.
pytestmark = pytest.mark.skipif(not has_abinit("7.9.0") or not has_pseudodojo,
                                reason="Requires abinit >= 7.9.0 and pseudodojo")


#@pytest.mark.parametrize("inp", [{"paral_kgb": 0}, {"paral_kgb": 1}])
def test_deltafactor(fwp):
    """Test the flow used for the computation of the deltafactor."""
    #from pymatgen.core.design_patterns import AttrDict
    #inp = AttrDict(inp)

    # Path of the pseudopotential to test.
    pseudo = abidata.pseudo("Si.GGA_PBE-JTH-paw.xml")

    flow = abilab.AbinitFlow(workdir=fwp.workdir, manager=fwp.manager)

    # Build the workflow for the computation of the deltafactor.
    # The workflow will produce a pdf file with the equation of state
    # and a file deltafactor.txt with the final results in the
    # outdir directory DELTAFACTOR/work_0/outdir.

    kppa = 20  # this value is for testing purpose (6570 is the correct one)
    ecut = 2
    pawecutdg = ecut * 2 if pseudo.ispaw else None

    from pseudo_dojo.dojo.deltaworks import DeltaFactory
    work = DeltaFactory().work_for_pseudo(pseudo, kppa=kppa, ecut=ecut, pawecutdg=pawecutdg)
    # Register the workflow.
    flow.register_work(work)
    flow.allocate()
    flow.build_and_pickle_dump()

    for task in flow[0]:
        task.start_and_wait()

    flow.check_status()
    flow.show_status()
    assert flow.all_ok
    assert all(work.finalized for work in flow)
    results = flow[0].get_results()
    #20.453 ang^3 88.545 GPa 4.31 20.8658081501 336.680999051 GPa -35.681897152
    #delta Equation of State: deltafactor_polyfit
    #Minimum volume = 20.87 Ang^3
    #modulus = 2.10 eV/Ang^3 = 336.68 GPa, b1 = -35.68
    #Deltafactor = 15.681 meV
    #assert 0


#@pytest.mark.parametrize("inp", [{"paral_kgb": 0}, {"paral_kgb": 1}])
def test_gbrv_flow(fwp):
    """The the GBRV flow: relaxation + EOS computation."""
    from pseudo_dojo.refdata.gbrv.gbrvworks import GbrvFactory
    factory = GbrvFactory()

    #pseudo = "si_pbe_v1_abinit.paw"
    pseudo = abidata.pseudo("Si.GGA_PBE-JTH-paw.xml")
    ecut = 2
    pawecutdg = 2 * ecut if pseudo.ispaw else None

    flow = abilab.AbinitFlow(workdir=fwp.workdir, manager=fwp.manager, pickle_protocol=0)

    struct_types = ["fcc"] #, "bcc"]

    for struct_type in struct_types:
        work = factory.relax_and_eos_work(pseudo, struct_type, ecut, pawecutdg=pawecutdg)
        flow.register_work(work)

    flow.allocate()
    flow.build_and_pickle_dump()

    work = flow[0]
    t0 = work[0]
    assert len(work) == 1

    t0.start_and_wait()
    flow.check_status()

    # At this point on_all_ok is called.
    assert t0.status == t0.S_OK
    assert len(flow) == 2
    assert len(flow[1]) == 9

    assert not flow.all_ok

    for task in flow[1]:
        task.start_and_wait()

    flow.check_status()
    flow.show_status()
    assert all(work.finalized for work in flow)
    assert flow.all_ok
    #assert 0

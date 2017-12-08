#!/usr/bin/env python
r"""
G0W0 Flow with factory functions
================================

G0W0 corrections with the HT interface.
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import sys
import os
import abipy.data as abidata
import abipy.flowtk as flowtk
from abipy import abilab


def build_flow(options):
    # Init structure and pseudos.
    structure = abilab.Structure.from_file(abidata.cif_file("si.cif"))
    pseudos = abidata.pseudos("14si.pspnc")

    # Working directory (default is the name of the script with '.py' removed and "run_" replaced by "flow_")
    if not options.workdir:
        options.workdir = os.path.basename(__file__).replace(".py", "").replace("run_", "flow_")

    # Initialize the flow.
    flow = flowtk.Flow(options.workdir, manager=options.manager)

    scf_kppa = 10
    nscf_nband = 10
    #nscf_ngkpt = [4,4,4]
    #nscf_shiftk = [0.0, 0.0, 0.0]
    ecut, ecuteps, ecutsigx = 4, 2, 3
    #scr_nband = 50
    #sigma_nband = 50

    multi = abilab.g0w0_with_ppmodel_inputs(
        structure, pseudos,
        scf_kppa, nscf_nband, ecuteps, ecutsigx,
        ecut=ecut, pawecutdg=None,
        accuracy="normal", spin_mode="unpolarized", smearing=None,
        #ppmodel="godby", charge=0.0, scf_algorithm=None, inclvkb=2, scr_nband=None,
        #sigma_nband=None, gw_qprange=1):

    )
    #multi.set_vars(paral_kgb=1)

    scf_input, nscf_input, scr_input, sigma_input = multi.split_datasets()
    work = flowtk.G0W0Work(scf_input, nscf_input, scr_input, sigma_input)
    flow.register_work(work)

    return flow


# This block generates the thumbnails in the Abipy gallery.
# You can safely REMOVE this part if you are using this script for production runs.
if os.getenv("GENERATE_SPHINX_GALLERY", False):
    __name__ = None
    import tempfile
    options = flowtk.build_flow_main_parser().parse_args(["-w", tempfile.mkdtemp()])
    build_flow(options).plot_networkx(tight_layout=True)


@flowtk.flow_main
def main(options):
    """
    This is our main function that will be invoked by the script.
    flow_main is a decorator implementing the command line interface.
    Command line args are stored in `options`.
    """
    return build_flow(options)


if __name__ == "__main__":
    sys.exit(main())

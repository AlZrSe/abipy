#!/usr/bin/env python
from __future__ import division, print_function

import os
import abipy.abilab as abilab


class QptdmWorkflow(abilab.Workflow):
    """
    This workflow is used for parallelizing the calculation of the 
    q-points of the screening. It also provides a finalize method 
    that calls mrgscr to merge the partial screening files.
    """
    def __init__(self, workdir, manager, wfk_file):
        super(QptdmWorkflow, self).__init__(workdir, manager)

        self.wfk_file = os.path.abspath(wfk_file)

    def build(self):
        super(QptdmWorkflow, self).build()

        for task in self:
            task.inlink_file(self.wfk_file)

    def finalize(self):
        #if not self.all_ok()
        #    return 

        scr_files = []
        for task in self:
            scr = task.outdir.has_abifile("SCR")
            scr_files.append(scr)

        print(scr_files)
        mrgscr = abilab.Mrgscr(verbose=1)
        mrgscr.merge_qpoints(scr_files, out_prefix="out_hello", cwd=None)


def build_qptdm_workflow(workdir, manager, scr_input, wfk_file):
    """
    Factory function that builds a `QptdmWorkflow`.

    Args:
        workdir:
            Working directory. 
        manager:
            `TaskManager` object.
        scr_input:
            Input for the screening calculation.
        wfk_file:
            Path to the ABINIT wavefunction file to use 
            for the computation of the screening

    Return
        `QptdmWorflow` object.
    """
    # Build a temporary workflow with a shell manager just to run 
    # ABINIT to get the list of q-points for the screening.
    shell_manager = manager.to_shell_manager(mpi_ncpus=1, policy=dict(autoparal=0))

    fake_input = scr_input.deepcopy()

    w = abilab.Workflow(workdir=os.path.join(workdir, "qptdm_run"), manager=shell_manager)
    w.register(fake_input)
    w.build()

    # Create the symbolic link and add the magic value nqpdm = -1 to 
    # get the list of q-points
    fake_task = w[0]
    fake_task.inlink_file(wfk_file)
    fake_task.strategy.add_extra_abivars({"nqptdm": -1})

    #print(scr_input)
    #print(fake_task.strategy.make_input())
    w.start()

    # Parse the section with the q-points
    qpoints = yaml_kpoints(fake_task.log_file.path, tag="<QPTDM>")
    print(qpoints)

    # Now we can build the final workflow.
    work = QptdmWorkflow(workdir, manager, wfk_file)

    for qpoint in qpoints:
        qptdm_input = scr_input.deepcopy()
        qptdm_input.set_variables(
            nqptdm=1,
            qptdm=qpoint
            #qptdm=qpoint.frac_coords,
        )
        work.register(qptdm_input)

    return work


def yaml_kpoints(filename, tag="<KPOINTS>"):
    end_tag = tag.replace("<", "</")

    with open(filename, "r") as fh:
        lines = fh.readlines()

    start, end = None, None
    for i, line in enumerate(lines):
        if tag in line:
            start = i
        elif end_tag in line:
            end = i
            break
                                                                                                             
    if start is None or end is None:
        raise ValueError("%s\n does not contain any valid %s section" % (filename, tag))
                                                                                                             
    if start == end:
        # Empy section ==> User didn't enable Yaml in ABINIT.
        raise ValueError("%s\n contains an empty RUN_HINTS section. Enable Yaml support in ABINIT" % filename)

    s = "".join(l for l in lines[start+1:end])

    import yaml
    try:
        d = yaml.load(s)
    except Exception as exc:
        raise ValueError("Malformatted Yaml section in file %s:\n %s" % (filename, str(exc)))

    import numpy as np
    return np.array(d["reduced_coordinates_of_qpoints"])
    #return KpointList(reciprocal_lattice, frac_coords, weights=None, names=None)

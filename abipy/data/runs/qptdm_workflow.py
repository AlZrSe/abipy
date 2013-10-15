#!/usr/bin/env python
from __future__ import division, print_function

import os
import time
import collections
import yaml
import numpy as np

from abipy.abilab import AbinitFlow, Mrgscr, Mrgddb, Mrggkk

from pymatgen.io.abinitio.tasks import ScfTask, PhononTask
from pymatgen.io.abinitio.workflows import Workflow, BandStructureWorkflow, IterativeWorkflow, PhononWorkflow

import logging
logger = logging.getLogger(__name__)


class QptdmWorkflow(Workflow):
    """
    This workflow parallelizes the calculation of the q-points of the screening. 
    It also provides the callback `on_all_ok` that calls mrgscr to merge 
    all the partial screening files produced.
    """
    def fill(self, wfk_file, scr_input):
        """
        Create the SCR tasks and register them in self.

        Args:
            wfk_file:
                Path to the ABINIT WFK file to use for the computation of the screening.
            scr_input:
                Input for the screening calculation.

        Return:
            self
        """
        assert len(self) == 0
        wfk_file = self.wfk_file = os.path.abspath(wfk_file)

        # Build a temporary workflow in the tmpdir that will use a shell manager 
        # to run ABINIT in order to get the list of q-points for the screening.
        shell_manager = self.manager.to_shell_manager(mpi_ncpus=1)

        w = Workflow(workdir=self.tmpdir.path_join("_qptdm_run"), manager=shell_manager)

        fake_input = scr_input.deepcopy()
        fake_task = w.register(fake_input)
        w.build()

        # Create the symbolic link and add the magic value 
        # nqpdm = -1 to the input to get the list of q-points.
        fake_task.inlink_file(wfk_file)
        fake_task.strategy.add_extra_abivars({"nqptdm": -1})
        w.start()

        # Parse the section with the q-points
        qpoints = yaml_read_kpoints(fake_task.log_file.path, tag="--- !Qptdms")
        #print(qpoints)
        w.rmtree()

        # Now we can register the task for the different q-points 
        for qpoint in qpoints:
            qptdm_input = scr_input.deepcopy()
            qptdm_input.set_variables(
                nqptdm=1,
                qptdm=qpoint
            )
            self.register(qptdm_input, manager=self.manager)

        return self.allocate()

    def merge_scrfiles(self):
        """
        This method is called when all the q-points have been computed.
        It runs `mrgscr` in sequential on the local machine to produce
        the final SCR file in the outdir of the `Workflow`.
        """
        scr_files = filter(None, [task.outdir.has_abiext("SCR") for task in self])

        logger.debug("will call mrgscr to merge %s:\n" % str(scr_files))
        assert len(scr_files) == len(self)

        mrgscr = Mrgscr(verbose=1)
        final_scr = mrgscr.merge_qpoints(scr_files, out_prefix="out", cwd=self.outdir.path)

    def on_all_ok(self):
        """
        This method is called when all the q-points have been computed.
        It runs `mrgscr` in sequential on the local machine to produce
        the final SCR file in the outdir of the `Workflow`.
        """
        final_scr = self.merge_scrfiles()

        results = dict(
            returncode=0,
            message="mrgscr done",
            final_scr=final_scr,
        )

        return results


def phonon_flow(workdir, manager, scf_input, ph_inputs):
    """
    Build an `AbinitFlow` for phonon calculations.

    Args:
        workdir:
            Working directory.
        manager:
            `TaskManager` object used to submit the jobs
        scf_input:
            Input for the GS SCF run.
        ph_inputs:
            List of Inpus for the phonon runs.

    Returns:
        `AbinitFlow`
    """
    natom = len(scf_input.structure)

    # Create the container that will manage the different workflows.
    flow = AbinitFlow(workdir, manager)

    # Register the first workflow (GS calculation)
    scf_task = flow.register_task(scf_input, task_class=ScfTask)

    # Build a temporary workflow with a shell manager just to run 
    # ABINIT to get the list of irreducible pertubations for this q-point.
    shell_manager = manager.to_shell_manager(mpi_ncpus=1)

    if not isinstance(ph_inputs, (list, tuple)):
        ph_inputs = [ph_inputs]

    for i, ph_input in enumerate(ph_inputs):
        fake_input = ph_input.deepcopy()

        tmp_dir = os.path.join(workdir, "__ph_run" + str(i) + "__")
        w = Workflow(workdir=tmp_dir, manager=shell_manager)
        fake_task = w.register(fake_input)

        # Use the magic value paral_rf = -1 
        # to get the list of irreducible perturbations for this q-point.
        vars = dict(paral_rf=-1,
                    rfatpol=[1, natom],  # Set of atoms to displace.
                    rfdir=[1, 1, 1],     # Along this set of reduced coordinate axis.
                   )

        fake_task.strategy.add_extra_abivars(vars)

        w.build()
        w.start()

        # Parse the file to get the perturbations.
        irred_perts = yaml_read_irred_perts(fake_task.log_file.path)
        print(irred_perts)
        #w.rmtree()

        # Now we can build the final list of workflows:
        # One workflow per q-point, each workflow computes all 
        # the irreducible perturbations for a singe q-point.
        work_qpt = PhononWorkflow()

        for irred_pert in irred_perts:
            print(irred_pert)
            new_input = ph_input.deepcopy()

            #rfatpol   1 1   # Only the first atom is displaced
            #rfdir   1 0 0   # Along the first reduced coordinate axis
            qpt = irred_pert["qpt"]
            idir = irred_pert["idir"]
            ipert = irred_pert["ipert"]

            # TODO this will work for phonons, but not for the other types of perturbations.
            rfdir = 3 * [0]
            rfdir[idir -1] = 1
            rfatpol = [ipert, ipert]

            new_input.set_variables(
                #rfpert=1,
                qpt=qpt,
                rfdir=rfdir,
                rfatpol=rfatpol,
            )

            work_qpt.register(new_input, deps={scf_task: "WFK"}, task_class=PhononTask)

        flow.register_work(work_qpt)
                                            
    return flow.allocate()


#class IrredPert(object):
#    def to_abivars(self):
#        #rfatpol   1 1   # Only the first atom is displaced
#        #rfdir   1 0 0   # Along the first reduced coordinate axis
#        qpt = irred_pert["qpt"]
#        idir = irred_pert["idir"]
#        ipert = irred_pert["ipert"]
#        return vars


def cbk_qptdm_workflow(flow, work, cbk_data):
    scr_input = cbk_data["input"]
    # Use the WFK file produced by the second 
    # Task in the first Workflow (NSCF step).
    nscf_task = flow[0][1]
    wfk_file = nscf_task.outdir.has_abiext("WFK")

    work.fill(wfk_file, scr_input)
    #work.add_deps(cbk.deps)
    work.connect_signals()
    work.build()

    return work


def g0w0_flow_with_qptdm(workdir, manager, scf_input, nscf_input, scr_input, sigma_input):
    """
    Build an `AbinitFlow` for one-shot G0W0 calculations.
    The computation of the q-points for the screening is parallelized with qptdm (task parallelism).

    Args:
        workdir:
            Working directory.
        manager:
            `TaskManager` object used to submit the jobs
        scf_input:
            Input for the GS SCF run.
        nscf_input:
            Input for the NSCF run (band structure run).
        scr_input:
            Input for the SCR run.
        sigma_input:
            Input for the SIGMA run.

    Returns:
        `AbinitFlow`
    """                                                      
    # Create the container that will manage the different workflows.
    flow = AbinitFlow(workdir, manager)

    # Register the first workflow (GS + NSCF calculation)
    bands_work = flow.register_work(BandStructureWorkflow(scf_input, nscf_input))

    assert not bands_work.scf_task.depends_on(bands_work.scf_task)
    assert bands_work.nscf_task.depends_on(bands_work.scf_task)

    # Register the callback that will be executed the workflow for the SCR with qptdm.
    scr_work = flow.register_cbk(cbk=cbk_qptdm_workflow, cbk_data={"input": scr_input},
                                 deps={bands_work.nscf_task: "WFK"}, work_class=QptdmWorkflow
                                )
                             
    assert scr_work.depends_on(bands_work.nscf_task)
    assert not scr_work.depends_on(bands_work.scf_task)

    # The last workflow contains a single SIGMA task that will use 
    # the data produced in the previous two workflows.
    sigma_task = flow.register_task(sigma_input, deps={bands_work.nscf_task: "WFK", scr_work: "SCR"})

    flow.allocate()
    assert sigma_task.depends_on(bands_work.nscf_task)
    assert not sigma_task.depends_on(bands_work.scf_task)
    assert sigma_task.depends_on(scr_work)

    flow.show_dependencies()
    #print("sigma_work.deps", sigma_work.deps)
    print("sigma_task.deps", sigma_task.deps)

    return flow


class YamlDoc(object):
    """A string with a YAML tag."""

    def __init__(self, string):
        self.string = string 
        self.tag = None

    #def __repr__(self):
    #    return self.string

    def __str__(self):
        return self.string


class YamlFileReaderError(Exception):
    """Exception raised by `YamlFileReader`."""


class YamlFileReader(collections.Iterator):
    """
    A file locking mechanism that has context-manager support 
    so you can use it in a with statement. 
    """
    Error = YamlFileReaderError

    def __init__(self, filename):
        self.stream = open(filename, "r")

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        self.stream.close()

    def seek(self, offset, whence=0):
        """
        seek(offset[, whence]) -> None.  Move to new file position.

        Argument offset is a byte count.  Optional argument whence defaults to
        0 (offset from start of file, offset should be >= 0); other values are 1
        (move relative to current position, positive or negative), and 2 (move
        relative to end of file, usually negative, although many platforms allow
        seeking beyond the end of a file).  If the file is opened in text mode,
        only offsets returned by tell() are legal.  Use of other offsets causes
        undefined behavior.
        Note that not all file objects are seekable.
        """
        return self.stream.seek(offset, whence)

    def all_yaml_docs(self):
        """
        Returns a list with all the YAML docs found. Seek the stream before returning.
        """
        docs = all_yaml_docs(self.stream)
        self.seek(0)
        return docs

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def next(self):
        """Return the next YAML document in stream."""
        return next_yaml_doc(self.stream)

    def next_doc_with_tag(self, doc_tag):
        """
        Returns the next document with the specified tag.
        Empty string is no doc is found.
        """
        for doc in self:
            if doc_tag in doc:
                return doc
        else:
            return ""

    def all_docs_with_tag(self, doc_tag, seek=True):
        """
        Returns all the documents with the specified tag.
        """
        docs = []

        while True:
            try:
                doc = self.next_doc_with(doc_tag)
                docs.append(doc)

            except StopIteration():
                break

        if seek:
            self.seek(0)
        
        return docs


def all_yaml_docs(stream):
    """
    Returns a list with all the YAML documents found in stream.

    .. warning:

        Assume that all the YAML docs (with the exception of the last one) 
        are closed explicitely with the sentinel '...'
    """
    docs, in_doc = [], False

    for line in stream:
        if line.startswith("---"):
            doc, in_doc = [], True

        if in_doc:
            doc.append(line)

        if in_doc and line.startswith("..."):
            in_doc = False
            docs.append("".join(doc))
            doc = []

    if doc:
        docs.append("".join(doc))

    return docs


def next_yaml_doc(stream, doc_tag="---"):
    """
    Returns the first YAML document in stream.

    .. warning:

        Assume that the YAML document are closed explicitely with the sentinel '...'
    """
    in_doc, lines = None, []
    for i, line in enumerate(stream):
        if line.startswith(doc_tag):
            in_doc = True

        if in_doc:
            lines.append(line)

        if in_doc and line.startswith("..."):
            break

    if lines:
        return "".join(lines)
    else:
        raise StopIteration()


def yaml_read_kpoints(filename, doc_tag="!Kpoints"):

    with YamlFileReader(filename) as r:
        doc = r.next_doc_with_tag(doc_tag)
        #doc = doc.replace(doc_tag, "")
        d = yaml.load(doc)

        return np.array(d["reduced_coordinates_of_qpoints"])
        #return KpointList(reciprocal_lattice, frac_coords, weights=None, names=None)


def yaml_read_irred_perts(filename, doc_tag="!IrredPerts"):

    with YamlFileReader(filename) as r:
        doc = r.next_doc_with_tag(doc_tag)
        #doc = doc.replace(doc_tag, "")
        print("doc",doc)
        d = yaml.load(doc)

        return d ["irred_perts"]


if __name__ == "__main__":

    string = """
---
none: [~, null]
bool: [true, false, on, off]
int: 42
float: 3.14159
list: [LITE, RES_ACID, SUS_DEXT]
dict: {hp: 13, sp: 5}
...

this is not a YAML document!
and the reader will ignore it

--- !Monster
name: Cave spider
hp: [2,6]    # 2d6
ac: 16
attacks: [BITE, HURT]
...

This is not a proper document since it does not start with --- 
the end tag below is ignored 
...
--- !Monster
name: Dragon
hp: [2,6]    # 2d6
ac: 32
attacks: [BITE, HURT]
...
"""
    print(string)

    filename = "foo.yaml"
    with open(filename, "w") as fh:
        fh.write(string)

    with YamlFileReader(filename) as r:

        # Read all docs present in file.
        all_docs = r.all_yaml_docs()
        print(all_docs)
        assert len(all_docs) == 3

        # We should be at the begining at the file.
        assert all_docs == r.all_yaml_docs()

        # Generate the docs
        r.seek(0)
        for i, doc in enumerate(r):
            print("doc", doc, "all", all_docs[i])
            assert doc == all_docs[i]

        # Find documents by tag.
        r.seek(0)
        monster = r.next_doc_with_tag("!Monster")
        assert monster == all_docs[1]

        monster = r.next_doc_with_tag("!Monster")
        assert monster == all_docs[2]

        monster = r.next_doc_with_tag("!Monster")
        assert monster == ""
    

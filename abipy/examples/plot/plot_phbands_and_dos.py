#!/usr/bin/env python
#
# This example shows how to plot the phonon band structure of AlAs.
# See tutorial/lesson_rf2.html

# FIXME: LO-TO splitting and phonon displacements instead of eigenvectors.
from abipy.abilab import PhononBands, PhdosReader, PhdosFile
import abipy.data as abidata

# Path to the PHBST file produced by anaddb.
phbst_file = abidata.ref_file("trf2_5.out_PHBST.nc")

# Create the object from file.
phbands = PhononBands.from_file(phbst_file)

# Read the Phonon DOS from the netcd file produced by anaddb (prtdos 2)
phdos_file = abidata.ref_file("trf2_5.out_PHDOS.nc")

with PhdosReader(phdos_file) as r:
    phdos = r.read_phdos()

# plot phonon bands and DOS.
phbands.plot_with_phdos(phdos, title="AlAs Phonon bands and DOS")

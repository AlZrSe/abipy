#!/usr/bin/env python
r"""
Phonon fatbands
===============

This example shows how to plot the phonon fatbands of AlAs.
See tutorial/lesson_rf2.html
"""
from abipy.abilab import abiopen
import abipy.data as abidata

# Open the PHBST file produced by anaddb and get the phonon bands.
with abiopen(abidata.ref_file("trf2_5.out_PHBST.nc")) as ncfile:
    phbands = ncfile.phbands

# Plot the phonon band structure.
phbands.plot_fatbands(title="AlAs phonon fatbands without LO-TO splitting")

# Plot the phonon band structure + PJDOS
# sphinx_gallery_thumbnail_number = 2
phdos_path = abidata.ref_file("trf2_5.out_PHDOS.nc")
phbands.plot_fatbands(units="Thz", phdos_file=phdos_path, title="AlAs phonon fatbands with PJDOS")


# Plot contributions to the phonon displacement at the Gamma point grouped by atom type.
phbands.plot_phdispl(qpoint=(0, 0, 0), units="meV")

# Decompose contributions along the three Cartesian directions.
phbands.plot_phdispl_cartdirs(qpoint=(0, 0, 0), units="cm-1")

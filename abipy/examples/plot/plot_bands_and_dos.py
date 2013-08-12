#!/usr/bin/env python
#
# This example shows how to compute the DOS and how to plot a band structure
# using two GSR files produced by abinit.
from abipy import abiopen
import abipy.data as data

# Open the file with energies computed on a k-path in the BZ
# and extract the band structure.
nscf_file = abiopen(data.ref_file("si_nscf_GSR.nc"))

nscf_ebands = nscf_file.ebands

# Open thefile with energies computed with a homogeneous sampling of the BZ 
# and extract the band structure.
gs_file = abiopen(data.ref_file("si_scf_GSR.nc"))

gs_ebands = gs_file.ebands

# Compute the DOS with the Gaussian method (use default values for 
# the broadening and the linear mesh step.
edos = gs_ebands.get_edos()

# Define the mapping reduced_coordinates -> name of the k-point.
klabels = {
    (0.5,  0.0,  0.0) : "L",
    (0.0,  0.0,  0.0) : "$\Gamma$",
    (0.0,  0.5,  0.5) : "X",
}

# Plot bands and DOS.
# Note that the NSCF run contains more bands that the SCF.
# This explains why the DOS is zero for e > 10.
nscf_ebands.plot_with_edos(edos, klabels=klabels)

# This example shows how to compute the DOS and how to plot a band structure
# using two netCDF WFK files produced by abinit.
from abipy import *

# Open the wavefunction file computed on a k-path in the BZ
# and extract the band structure.
nscf_filename = get_ncfile("si_nscf_WFK-etsf.nc")

nscf_wfk = WFK_File(nscf_filename)

nscf_bands = nscf_wfk.get_bands()

# Open the wavefunction file computed with a homogeneous sampling of the BZ 
# and extract the band structure on the k-mesh.
gs_filename = get_ncfile("si_WFK-etsf.nc")

gs_wfk = WFK_File(gs_filename)

gs_bands = gs_wfk.get_bands()

# Compute the DOS with the Gaussian method.
dos = gs_bands.get_dos()

# Define the mapping reduced_coordinates -> label of the k-point.
klabels = {
    (0.5,  0.0,  0.0) : "L",
    (0.0,  0.0,  0.0) : "$\Gamma$",
    (0.0,  0.5,  0.5) : "X",
}

# Plot bands and DOS.
# Note that the NSCF run contains more bands that the SCF.
# This explains why the DOS is zero for e > 10.
nscf_bands.plot_with_dos(dos, klabels=klabels)

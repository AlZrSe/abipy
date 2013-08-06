#!/usr/bin/env python
#
# This example shows how to display the Brillouin zone 
# with pymatgen and matplotlib.
from abipy import *

# Open the WKF file.
wfk_file = WFK_File(get_ncfile("si_nscf_WFK-etsf.nc"))

# Extract the crystalline structure.
structure = wfk_file.structure

# Visualize the BZ.
structure.show_bz()

#from pprint import pprint
#pprint(structure.hsym_kpoints)

#print("kpath")
#pprint(structure.hsym_kpoint.get_kpoints())

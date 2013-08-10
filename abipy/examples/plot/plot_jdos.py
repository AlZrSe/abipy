#!/usr/bin/env python
#
# This example shows how plot the different contributions 
# to the electronic joint density of states of Silicon
from abipy import *
import abipy.data as data

# Extract the bands computed with the SCF cycle on a Monkhorst-Pack mesh.
wfk = WFK_File(data.ref_file("si_scf_WFK-etsf.nc"))
ebands = wfk.ebands

# Select the valence and conduction bands to include in the JDOS
# Here we include valence bands from 0 to 3 and the first conduction band (4).
vrange = range(0,4)
crange = range(4,5)

# Plot data.
ebands.plot_ejdosvc(vrange, crange)

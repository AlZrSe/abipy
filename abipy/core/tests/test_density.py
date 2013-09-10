#!/usr/bin/env python
"""Tests for core.density module"""
from __future__ import print_function, division

import abipy.data as data 

from abipy.core import Density
from abipy.core.testing import *
from abipy.iotools import *


class TestDensity(AbipyTest):
    """Unit tests for Density."""

    def test_ncread_density(self):
        """Read density from NC example data files"""
        assert data.DEN_NCFILES

        for path in data.DEN_NCFILES:
            print("Reading DEN file %s " % path)

            # Read data directly from file.
            with ETSF_Reader(path) as r:
                nelect_file = r.read_value("number_of_electrons")

            # Compute nelect from data.
            den = Density.from_file(path)
            structure = den.structure
            print(den)
            rhor_tot = den.get_rhor_tot()
            rhog_tot = den.get_rhog_tot()
            nelect_calc = den.get_nelect().sum()

            # Diff between nelect computed and the one written on file.
            self.assert_almost_equal(nelect_calc, nelect_file)
            self.assert_almost_equal(rhog_tot[0,0,0] * structure.volume, nelect_file)

            if self.which("xcrysden") is not None:
                # Export data in xsf format.
                visu = den.export(".xsf")
                self.assertTrue(callable(visu))


if __name__ == "__main__":
    import unittest
    unittest.main()

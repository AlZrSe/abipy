"""Tests for symmetries module"""
from __future__ import print_function, division

import numpy as np
import abipy.data as data

from abipy.core import Structure
from abipy.core.symmetries import *
from abipy.core.testing import *

class TestSymmetries(AbipyTest):
    """"Test symmetries."""

    def test_silicon(self):
        """Test silicon space group."""
        structure = Structure.from_file(data.ref_file("si_scf_WFK-etsf.nc"))

        self.assertTrue(structure.has_spacegroup)
        self.assertTrue(structure.is_symmorphic)

        self.serialize_with_pickle(structure, protocols=[-1])

        spgrp = structure.spacegroup
        print("spgrp:\n", spgrp)

        #print("mult_tables:\n", spgrp.mult_table)
        classes = spgrp.classes

        self.assertEqual(sum(len(c) for c in spgrp.classes), len(spgrp))

        # Operation in the same class have the same trace and determinant.
        for cls in classes: 
            print(cls)
            isym0 = cls[0]
            ref_trace = spgrp[isym0].trace
            ref_det = spgrp[isym0].det
            for isym in cls[1:]:
                self.assertEqual(spgrp[isym].trace, ref_trace) 
                self.assertEqual(spgrp[isym].det, ref_det) 

        #assert 0

        self.assertTrue(spgrp == spgrp)
        self.assertTrue(spgrp.spgid == 227)
        self.assertTrue(spgrp.has_timerev)
        self.assertTrue(len(spgrp) == 48 * 2)
        self.assertTrue(spgrp.num_spatial_symmetries == 48)

        self.assertTrue(spgrp.is_group())
        # TODO
        #si_symrel = 
        si_tnons = np.reshape(24 * [0, 0, 0, 0.25, 0.25, 0.25], (48, 3))
        si_symafm = np.ones(48, dtype=np.int)

        self.assert_almost_equal(si_tnons, spgrp.tnons)
        self.assert_almost_equal(si_symafm, spgrp.symafm)

        for (idx, symmop) in enumerate(spgrp):
            self.assertTrue(symmop in spgrp)
            self.assertTrue(spgrp.count(symmop) == 1)
            self.assertTrue(spgrp.find(symmop) == idx)
            self.assertTrue(abs(symmop.det) == 1)

        for idx in range(len(spgrp)-1):
            self.assertTrue(spgrp[idx] == spgrp[idx])
            self.assertTrue(spgrp[idx] != spgrp[idx+1])

        for fmop in spgrp.fm_symmops:
            self.assertTrue(fmop.is_fm)

        ucell_coords = np.reshape([site.frac_coords for site in structure], (len(structure), 3))

        err_msg = ""
        for site in structure:
            for symop in spgrp:
                rot_coords = symop.rotate_r(site.frac_coords, in_ucell=True)

                for atom_coords in ucell_coords:
                    #print (atom_coords - rot_coords)
                    if np.allclose(atom_coords,  rot_coords):
                        break
                else:
                    err_msg += "Cannot find symmetrical image of %s\n" % str(rot_coords)

                self.assertFalse(err_msg)

        # Test little group.
        ltg_symmops, g0vecs, isyms = spgrp.get_little_group(kpoint=[0,0,0])

        self.assertTrue(len(ltg_symmops) == len(spgrp))

        for o1, o2 in zip(ltg_symmops, spgrp):
            self.assertEqual(o1, o2)


class LatticeRotationTest(AbipyTest):
    def test_base(self):
        """Test LatticeRotation."""
        E = LatticeRotation([1, 0, 0,
                             0, 1, 0,
                             0, 0, 1])

        I = LatticeRotation([-1,  0,  0,
                              0, -1,  0,
                              0,  0, -1])

        self.assertTrue(E.isE and E.is_proper and E.inverse() == E)
        self.assertTrue(I.isI and not I.is_proper and I.inverse() == I)

        # Basic operations
        atrue = self.assertTrue

        atrue(E != I)
        atrue(+E == E)
        atrue(-I == E)
        atrue(E * I == I) 
        atrue(I ** 0 == E)
        atrue(I ** 3 == I)

        # Test pickle.
        self.serialize_with_pickle([E, I])


# reduced_symmetry_matrices =
#  1, 0, 0,
#  0, 1, 0,
#  0, 0, 1,
#  -1, 0, 0,
#  0, -1, 0,
#  0, 0, -1,
#  0, -1, 1,
#  0, -1, 0,
#  1, -1, 0,
#  0, 1, -1,
#  0, 1, 0,
#  -1, 1, 0,
#  -1, 0, 0,
#  -1, 0, 1,
#  -1, 1, 0,
#  1, 0, 0,
#  1, 0, -1,
#  1, -1, 0,
#  0, 1, -1,
#  1, 0, -1,
#  0, 0, -1,
#  0, -1, 1,
#  -1, 0, 1,
#  0, 0, 1,
#  -1, 0, 0,
#  -1, 1, 0,
#  -1, 0, 1,
#  1, 0, 0,
#  1, -1, 0,
#  1, 0, -1,
#  0, -1, 1,
#  1, -1, 0,
#  0, -1, 0,
#  0, 1, -1,
#  -1, 1, 0,
#  0, 1, 0,
#  1, 0, 0,
#  0, 0, 1,
#  0, 1, 0,
#  -1, 0, 0,
#  0, 0, -1,
#  0, -1, 0,
#  0, 1, -1,
#  0, 0, -1,
#  1, 0, -1,
#  0, -1, 1,
#  0, 0, 1,
#  -1, 0, 1,
#  -1, 0, 1,
#  -1, 1, 0,
#  -1, 0, 0,
#  1, 0, -1,
#  1, -1, 0,
#  1, 0, 0,
#  0, -1, 0,
#  1, -1, 0,
#  0, -1, 1,
#  0, 1, 0,
#  -1, 1, 0,
#  0, 1, -1,
#  1, 0, -1,
#  0, 0, -1,
#  0, 1, -1,
#  -1, 0, 1,
#  0, 0, 1,
#  0, -1, 1,
#  0, 1, 0,
#  0, 0, 1,
#  1, 0, 0,
#  0, -1, 0,
#  0, 0, -1,
#  -1, 0, 0,
#  1, 0, -1,
#  0, 1, -1,
#  0, 0, -1,
#  -1, 0, 1,
#  0, -1, 1,
#  0, 0, 1,
#  0, -1, 0,
#  0, -1, 1,
#  1, -1, 0,
#  0, 1, 0,
#  0, 1, -1,
#  -1, 1, 0,
#  -1, 0, 1,
#  -1, 0, 0,
#  -1, 1, 0,
#  1, 0, -1,
#  1, 0, 0,
#  1, -1, 0,
#  0, 1, 0,
#  1, 0, 0,
#  0, 0, 1,
#  0, -1, 0,
#  -1, 0, 0,
#  0, 0, -1,
#  0, 0, -1,
#  0, 1, -1,
#  1, 0, -1,
#  0, 0, 1,
#  0, -1, 1,
#  -1, 0, 1,
#  1, -1, 0,
#  0, -1, 1,
#  0, -1, 0,
#  -1, 1, 0,
#  0, 1, -1,
#  0, 1, 0,
#  0, 0, 1,
#  1, 0, 0,
#  0, 1, 0,
#  0, 0, -1,
#  -1, 0, 0,
#  0, -1, 0,
#  -1, 1, 0,
#  -1, 0, 0,
#  -1, 0, 1,
#  1, -1, 0,
#  1, 0, 0,
#  1, 0, -1,
#  0, 0, 1,
#  0, 1, 0,
#  1, 0, 0,
#  0, 0, -1,
#  0, -1, 0,
#  -1, 0, 0,
#  1, -1, 0,
#  0, -1, 0,
#  0, -1, 1,
#  -1, 1, 0,
#  0, 1, 0,
#  0, 1, -1,
#  0, 0, -1,
#  1, 0, -1,
#  0, 1, -1,
#  0, 0, 1,
#  -1, 0, 1,
#  0, -1, 1,
#  -1, 1, 0,
#  -1, 0, 1,
#  -1, 0, 0,
#  1, -1, 0,
#  1, 0, -1,
#  1, 0, 0 ;


if __name__ == "__main__": 
    import unittest
    unittest.main()

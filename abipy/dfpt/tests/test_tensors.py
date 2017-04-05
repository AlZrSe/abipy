"""Tests for phonons"""
from __future__ import print_function, division, unicode_literals, absolute_import

import os
import numpy as np

from abipy.core.testing import *
from abipy.dfpt.tensors import DielectricTensor, NLOpticalSusceptibilityTensor
import abipy.data as abidata


class NLOpticalSusceptibilityTensorTest(AbipyTest):

    def test_base(self):
        """Base tests for NLOpticalSusceptibilityTensor"""
        anaddbnc_fname = abidata.ref_file("AlAs_nl_dte_anaddb.nc")

        NLOpticalSusceptibilityTensor.from_file(anaddbnc_fname)


class DielectricTensorTest(AbipyTest):

    def test_base(self):
        """Base tests for DielectricTensor"""
        dt = DielectricTensor(np.diag([1,2,3]))

        self.assertArrayAlmostEqual(dt.reflectivity(), [0., 0.029437251522859434, 0.071796769724490825])
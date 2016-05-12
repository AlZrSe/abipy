from __future__ import division, print_function, unicode_literals
import unittest
import shutil
import os
import tempfile
from pymatgen.util.testing import PymatgenTest
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.GWvaspinputsets import GWDFTDiagVaspInputSet, GWG0W0VaspInputSet, GWscDFTPrepVaspInputSet
from pymatgen.io.vasp.GWvaspinputsets import SingleVaspGWWork
from abipy.gw.datastructures import GWSpecs, GWConvergenceData, get_spec
from abipy.gw.codeinterfaces import AbinitInterface, VaspInterface, get_code_interface
from abipy.gw.tests.test_helpers import structure
from abipy.abilab import Structure as AbiStructure
from abipy.gw.GWworks import GWWork, SingleAbinitGWWork, VaspGWFWWorkFlow
import abipy.data as abidata
from pymatgen.io.vasp.inputs import get_potcar_dir
from pymatgen.io.abinit.flows import Flow

__author__ = 'setten'

POTCAR_DIR = get_potcar_dir()


class GWSpecTest(PymatgenTest):
    def test_GWspect(self):
        """
        Testing the class GWSpecs()
        """
        spec = GWSpecs()
        self.assertIsInstance(spec, GWSpecs)
        self.assertEqual(spec.get_code(), 'ABINIT')
        self.assertIsInstance(spec.code_interface, AbinitInterface)
        spec.data['code'] = 'VASP'
        spec.update_code_interface()
        self.assertEqual(spec.get_code(), 'VASP')
        self.assertIsInstance(spec.code_interface, VaspInterface)

    def test_GWspect_test(self):
        """
        Testing warnings and errors of gwspecs
        """
        spec = GWSpecs()
        spec.test()
        self.assertEqual(len(spec.warnings), 0)
        self.assertEqual(len(spec.errors), 0)

    def test_GWget_spec(self):
        """
        Testing the factory function get_specs()
        """
        spec = get_spec('GW')
        self.assertIsInstance(spec, GWSpecs)


class GWConvergenceDataTest(PymatgenTest):

    def test_GWConvergenceData(self):
        """
        Testing the class GWConvergenceData
        """
        spec = GWSpecs()
        self.assertIsInstance(structure, Structure)
        structure.item = 'mp-149'
        conv_data = GWConvergenceData(spec=spec, structure=structure)
        self.assertIsInstance(conv_data, GWConvergenceData)


class GWTestCodeInterfaces(PymatgenTest):
    def test_VaspInterface(self):
        """
        Testing the VASP code interface
        """
        interface = get_code_interface('VASP')
        self.assertIsInstance(interface, VaspInterface)
        self.assertEqual(len(interface.conv_pars), 3)
        self.assertEqual(len(interface.supported_methods), 4)
        # self.assertEqual(interface.get_conv_res_test(spec_data=spec.data, structure=structure), {})

    def test_AbinitInterface(self):
        """
        Testing the ANINIT code interface
        """
        interface = get_code_interface('ABINIT')
        self.assertIsInstance(interface, AbinitInterface)
        self.assertEqual(len(interface.conv_pars), 3)
        self.assertEqual(len(interface.supported_methods), 2)
        self.assertFalse(interface.all_done)
        self.assertEqual(interface.grid, 0)
        self.assertTrue(interface.hartree_parameters)
        self.assertFalse(interface.converged)
        self.assertEqual(len(interface.other_vars), 1166)
        self.assertEqual(interface.gw_data_file, 'out_SIGRES.nc')
        self.assertIsNone(interface.workdir)


class GWVaspInputSetTests(PymatgenTest):

    def setUp(self):
        """
        Testing GWVaspInputSetTests setUp
        """
        self.structure = structure
        self.spec = GWSpecs()
        self.spec.data['code'] = 'VASP'
        self.spec.update_code_interface()

    def test_GWscDFTPrepVaspInputSet(self):
        """
        Testing GWVaspInputSetTests GWscDFTPrepVaspInputSet
        """
        inpset = GWscDFTPrepVaspInputSet(structure=self.structure, spec=self.spec)
        self.assertIsInstance(inpset, GWscDFTPrepVaspInputSet)
        self.assertEqual(inpset.convs, {})

    @unittest.skipIf(POTCAR_DIR is None, "POTCAR dir is None")
    def test_GWDFTDiagVaspInputSet(self):
        """
        Testing GWVaspInputSetTests GWDFTDiagVaspInputSet
        """
        self.maxDiff = None
        inpset = GWDFTDiagVaspInputSet(structure=self.structure, spec=self.spec)
        self.assertIsInstance(inpset, GWDFTDiagVaspInputSet)
        self.assertEqual(inpset.convs,
                         {u'NBANDS': {u'test_range': (10, 20, 30, 40, 50, 60, 70), u'control': u'gap',
                                      u'method': u'set_nbands'}})

        self.assertEqual(inpset.incar_settings, {u'ALGO': u'Exact', u'EDIFF': 1e-10, u'IBRION': -1, u'ICHARG': 1,
                                                 u'ISMEAR': -5, u'ISPIN': 1, u'LOPTICS': u'TRUE', u'LORBIT': 11,
                                                 u'LREAL': u'AUTO', u'LWAVE': True, u'MAGMOM': {u'Co': 5, u'Cr': 5,
                                                 u'Fe': 5, u'Mn': 5, u'Mn3+': 4, u'Mn4+': 3, u'Mo': 5, u'Ni': 5,
                                                 u'V': 5, u'W': 5}, u'NBANDS': 240, u'NELM': 1, u'NPAR': 40,
                                                 u'PREC': u'Medium', u'SIGMA': 0.01})

    @unittest.skipIf(POTCAR_DIR is None, "POTCAR dir is None")
    def test_GWG0W0VaspInputSet(self):
        """
        Testing GWVaspInputSetTests GWG0W0VaspInputSet
        """
        inpset = GWG0W0VaspInputSet(structure=self.structure, spec=self.spec)
        self.assertIsInstance(inpset, GWG0W0VaspInputSet)
        self.assertEqual(inpset.convs,
                         {u'ENCUTGW': {u'test_range': (200, 400, 600, 800), u'control': u'gap', u'method': u'incar_settings'}})

    def test_SingleVaspGWWork(self):
        """
        Testing GWVaspInputSetTests SingleVaspGWWork
        """
        work = SingleVaspGWWork(structure=self.structure, spec=self.spec, job='prep')
        self.assertIsInstance(work, SingleVaspGWWork)


class GWworksTests(PymatgenTest):

    def test_GWWork(self):
        """
        Testing the abstract class GWFWWork
        """
        struc = AbiStructure.from_file(abidata.cif_file("si.cif"))
        struc.item = 'test'
        self.assertIsInstance(struc, AbiStructure)
        work = GWWork()
        work.set_status(struc)
        self.assertEqual(work.workdir, 'Si_test/work_0')
        self.assertEqual(work.grid, 0)
        self.assertFalse(work.all_done)

    def test_VaspGWFWWorkFlow(self):
        """
        Testing the concrete VaspGWFWWorkFlow class
        """
        struc = AbiStructure.from_file(abidata.cif_file("si.cif"))
        struc.item = 'test'
        self.assertIsInstance(struc, AbiStructure)
        work = VaspGWFWWorkFlow()

        self.assertEqual(len(work.work_list), 0)
        self.assertEqual(len(work.connections), 0)
        self.assertEqual(work.fw_id, 1)
        self.assertEqual(work.prep_id, 1)
        self.assertEqual(len(work.wf), 0)

        done = False

        if False:
            for job in ['prep', 'G0W0', 'GW0', 'scGW0']:
                parameters = dict()
                parameters['spec'] = dict()
                parameters['spec']['converge'] = True
                parameters['job'] = job
                work.add_work(parameters=parameters)

        # self.assertTrue(done, 'there are tests missing')

    def test_SingleAbinitGWWork(self):
        """
        Testing the concrete SingelAbinitGWWork class
        """
        struc = AbiStructure.from_file(abidata.cif_file("si.cif"))
        struc.item = 'test'

        wdir = tempfile.mkdtemp()
        print('wdir', wdir)

        os.chdir(wdir)
        shutil.copyfile(abidata.cif_file("si.cif"), os.path.join(wdir, 'si.cif'))
        shutil.copyfile(abidata.pseudo("14si.pspnc").path, os.path.join(wdir, 'Si.pspnc'))
        shutil.copyfile(os.path.join(abidata.dirpath, 'managers', 'shell_manager.yml'),
                        os.path.join(wdir, 'manager.yml'))
        shutil.copyfile(os.path.join(abidata.dirpath, 'managers', 'scheduler.yml'), os.path.join(wdir, 'scheduler.yml'))

        try:
            temp_ABINIT_PS_EXT = os.environ['ABINIT_PS_EXT']
            temp_ABINIT_PS = os.environ['ABINIT_PS']
        except KeyError:
            temp_ABINIT_PS_EXT = None
            temp_ABINIT_PS = None

        os.environ['ABINIT_PS_EXT'] = '.pspnc'
        os.environ['ABINIT_PS'] = wdir
        self.assertIsInstance(struc, AbiStructure)
        spec = get_spec('GW')
        work = SingleAbinitGWWork(struc, spec)
        self.assertEqual(len(work.CONVS), 3)

        spec = get_spec('GW')
        work = SingleAbinitGWWork(struc, spec)
        conv_strings = ['method', 'control', 'level']
        for test in work.CONVS:
            self.assertIsInstance(work.CONVS[test]['test_range'], tuple)
            for item in conv_strings:
                self.assertIsInstance(work.CONVS[test][item], unicode)
        self.assertEqual(work.work_dir, 'Si_test')
        self.assertEqual(len(work.pseudo_table), 1)
        self.assertEqual(work.bands_fac, 1)

        self.assertEqual(work.get_electrons(struc), 8)
        self.assertEqual(work.get_bands(struc), 6)
        self.assertGreater(work.get_bands(struc), work.get_electrons(struc) / 2, 'More electrons than bands, very bad.')

        flow = work.create()

        self.assertIsInstance(flow, Flow)

        if temp_ABINIT_PS is not None:
            os.environ['ABINIT_PS_EXT'] = temp_ABINIT_PS_EXT
            os.environ['ABINIT_PS'] = temp_ABINIT_PS

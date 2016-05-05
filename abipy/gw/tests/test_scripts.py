from __future__ import division, print_function, unicode_literals
import os
import shutil
import tempfile
import abipy.data as abidata
from pymatgen.util.testing import PymatgenTest
# from pymatgen.core.structure import Structure
# from pymatgen.io.vasp.GWvaspinputsets import GWDFTDiagVaspInputSet, GWG0W0VaspInputSet, GWscDFTPrepVaspInputSet
# from pymatgen.io.vasp.GWvaspinputsets import SingleVaspGWWork
from abipy.gw.datastructures import GWSpecs, get_spec  # , GWConvergenceData
# from abipy.gw.codeinterfaces import AbinitInterface, VaspInterface, get_code_interface
# from abipy.gw.tests.test_helpers import structure
from pymatgen.io.vasp.inputs import get_potcar_dir
POTCAR_DIR = get_potcar_dir()


__author__ = 'setten'


class GWSetupTest(PymatgenTest):
    def test_setup(self):
        """
        testing the main functions called in the abiGWsetup script
        """

        spec_in = get_spec('GW')
        self.assertIsInstance(spec_in, GWSpecs)

        self.assert_equal(spec_in.test(), 0)

        wdir = tempfile.mkdtemp()
        base = os.getcwd()
        print(wdir)

        os.chdir(wdir)

        shutil.copyfile(abidata.cif_file("si.cif"), os.path.join(wdir, 'si.cif'))
        shutil.copyfile(abidata.pseudo("14si.pspnc").path, os.path.join(wdir, 'Si.pspnc'))
        shutil.copyfile(os.path.join(abidata.dirpath, 'managers', 'shell_manager.yml'), os.path.join(wdir, 'manager.yml'))
        shutil.copyfile(os.path.join(abidata.dirpath, 'managers', 'scheduler.yml'), os.path.join(wdir, 'scheduler.yml'))
        spec_in.data['source'] = 'cif'
        print(abidata.dirpath)

        spec_in.write_to_file('spec.in')
        
        # broken due to strategy refactoring
        # spec_in.loop_structures('i')

        os.chdir(base)

        shutil.rmtree(wdir)

        # test the folder structure

        # read some of the input files

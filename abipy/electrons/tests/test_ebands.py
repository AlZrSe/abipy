"""Tests for electrons.ebands module"""
from __future__ import print_function, division, unicode_literals, absolute_import

import sys
import numpy as np
import unittest
import abipy.data as abidata
import pymatgen.core.units as units

from abipy.core.kpoints import KpointList
from abipy.electrons.ebands import (ElectronBands, ElectronDos, ElectronBandsPlotter, ElectronDosPlotter,
    ElectronsReader, frame_from_ebands)
from abipy.core.testing import AbipyTest


class EbandsReaderTest(AbipyTest):

    def test_reader(self):
        """Test ElectronsReader with WFK file."""

        with ElectronsReader(abidata.ref_file("si_scf_WFK.nc")) as r:
            kpoints = r.read_kpoints()
            assert isinstance(kpoints, KpointList)
            #assert len(kpoints) == ??
            #self.assert_all_equal(self.read_nband_sk == ??))

            eigens = r.read_eigenvalues()
            occfacts = r.read_occupations()
            fermie = r.read_fermie()
            #assert fermie ==
            assert r.read_nelect() == 8
            #smearing = r.read_smearing()


class ElectronBandsTest(AbipyTest):

    def test_nickel_ebands_spin(self):
        """Test Nickel electron bands with nsppol == 2"""
        ref_nelect = 18
        ni_ebands_kmesh = ElectronBands.from_file(abidata.ref_file("ni_666k_GSR.nc"))
        assert ElectronBands.as_ebands(ni_ebands_kmesh) is ni_ebands_kmesh

        repr(ni_ebands_kmesh); str(ni_ebands_kmesh)
        #assert ni_ebands_kmesh.smearing == "foo"
        assert ni_ebands_kmesh.nsppol == 2 and ni_ebands_kmesh.nspinor == 1 and ni_ebands_kmesh.nspden == 2
        assert ni_ebands_kmesh.nelect == ref_nelect
        assert ni_ebands_kmesh.kpoints.is_ibz and ni_ebands_kmesh.has_bzmesh and not ni_ebands_kmesh.has_bzpath
        assert ni_ebands_kmesh.has_timrev
        ni_ebands_kmesh.copy()
        ni_ebands_kmesh.deepcopy()

        ni_edos = ni_ebands_kmesh.get_edos()
        repr(ni_edos); str(ni_edos)

        ni_ebands_kpath = ElectronBands.from_file(abidata.ref_file("ni_kpath_GSR.nc"))

        repr(ni_ebands_kpath); str(ni_ebands_kpath)
        assert ni_ebands_kpath.nsppol == 2 and ni_ebands_kpath.nspinor == 1 and ni_ebands_kpath.nspden == 2
        assert ni_ebands_kpath.nelect == ref_nelect
        assert ni_ebands_kpath.kpoints.is_path and not ni_ebands_kpath.has_bzmesh and ni_ebands_kpath.has_bzpath
        assert ni_ebands_kpath.has_timrev
        assert ni_ebands_kpath.fermie == ni_ebands_kmesh.fermie

        # Serialization
        self.serialize_with_pickle(ni_ebands_kpath, test_eq=False)
        self.assertMSONable(ni_ebands_kpath, test_if_subclass=False)

        df = ni_ebands_kpath.to_pdframe()
        ni_ebands_kpath.to_xmgrace(self.get_tmpname(text=True))

        # BXSF cannot be produced because.
        #ngkpt    6 6 6
        #nshiftk  4
        #shiftk   1/2 1/2 1/2 1/2 0.0 0.0 0.0 1/2 0.0 0.0 0.0 1/2
        with self.assertRaises(ValueError):
            ni_ebands_kmesh.to_bxsf(self.get_tmpname(text=True))

        # Test plot methods
        if self.has_matplotlib():
            elims = [-10, 2]
            assert ni_ebands_kmesh.plot(show=False)
            assert ni_ebands_kmesh.show_bz(show=False)
            assert ni_ebands_kpath.plot(ylims=elims, show=False)
            assert ni_ebands_kpath.plot_with_edos(ni_edos, ylims=elims, show=False)
            assert ni_ebands_kpath.show_bz()
            assert ni_edos.plot(xlims=elims, show=False)
            assert ni_edos.plot_dos_idos(xlims=elims, show=False)
            assert ni_edos.plot_up_minus_down(xlims=elims, show=False)

            #vrange, crange = range(0, 4), range(4, 5)
            #assert ni_ebands_kmesh.plot_ejdosvc(vrange, crange, cumulative=False, show=False)
            #assert ni_ebands_kmesh.plot_ejdosvc(vrange, crange, cumulative=True, show=False)

            if self.has_seaborn():
                assert ni_ebands_kmesh.boxplot(brange=[5, 10], show=False,
                    title="Boxplot for up and down spin and 10 > band >= 5")

        # Test Abipy --> Pymatgen converter.
        # TODO: More tests
        pmg_bands_kpath = ni_ebands_kpath.to_pymatgen()
        pmg_bands_kmesh = ni_ebands_kmesh.to_pymatgen()

    def test_silicon_ebands(self):
        """Test electron bands with nsppol == 1"""
        si_ebands_kmesh = ElectronBands.from_file(abidata.ref_file("si_scf_GSR.nc"))
        assert not si_ebands_kmesh.has_metallic_scheme
        repr(si_ebands_kmesh); str(si_ebands_kmesh)
        assert si_ebands_kmesh.to_string(title="Title",
                with_structure=False, with_kpoints=True, verbose=1)

        for spin, ik, band in si_ebands_kmesh.skb_iter():
            assert spin == 0
            assert si_ebands_kmesh.nkpt >= ik >= 0
            assert si_ebands_kmesh.nband_sk[spin, ik] >= band >= 0

        # Test ElectronBands get_e0
        assert si_ebands_kmesh.get_e0("fermie") == si_ebands_kmesh.fermie
        assert si_ebands_kmesh.get_e0(None) == 0.0
        assert si_ebands_kmesh.get_e0("None") == 0.0
        assert si_ebands_kmesh.get_e0(1.0) == 1.0
        with self.assertRaises(ValueError):
            si_ebands_kmesh.get_e0("foo")

        dless_states = si_ebands_kmesh.dispersionless_states()
        assert not dless_states

        estats = si_ebands_kmesh.spacing()
        self.assert_almost_equal(estats.mean, 2.3100587301616917)
        self.assert_almost_equal(estats.stdev, 2.164400652355628)
        self.assert_almost_equal(estats.min, 0)
        self.assert_almost_equal(estats.max, 11.855874158768694)
        print(estats)

        si_edos = si_ebands_kmesh.get_edos()
        repr(si_edos); str(si_edos)
        assert ElectronDos.as_edos(si_edos, {}) is si_edos
        edos_samevals = ElectronDos.as_edos(si_ebands_kmesh, {})
        assert ElectronDos.as_edos(si_ebands_kmesh, {}) == si_edos
        assert ElectronDos.as_edos(abidata.ref_file("si_scf_GSR.nc"), {}) == si_edos
        with self.assertRaises(TypeError):
            ElectronDos.as_edos({}, {})

        mu = si_edos.find_mu(8)
        imu = si_edos.tot_idos.find_mesh_index(mu)
        self.assert_almost_equal(si_edos.tot_idos[imu][1], 8, decimal=2)

        d, i = si_edos.dos_idos(spin=0)
        tot_d, tot_i = si_edos.dos_idos()
        self.assert_almost_equal(2 * d.values, tot_d.values)
        self.assert_almost_equal(2 * i.values, tot_i.values)

        # Test ElectronDos get_e0
        assert si_edos.get_e0("fermie") == si_edos.fermie
        assert si_edos.get_e0(None) == 0.0
        assert si_edos.get_e0("None") == 0.0
        assert si_edos.get_e0(1.0) == 1.0
        with self.assertRaises(TypeError):
            si_edos.get_e0("foo")

        self.serialize_with_pickle(si_edos, protocols=[-1], test_eq=False)

        # Test plot methods
        if self.has_matplotlib():
            klabels = {
                (0,0,0): "$\Gamma$",
                (0.375, 0.375, 0.7500): "K",
                (0.5, 0.5, 1.0): "X",
                (0.5, 0.5, 0.5): "L",
                (0.5, 0.0, 0.5): "X",
                (0.5, 0.25, 0.75): "W",
            }

            assert si_edos.plot(show=False)
            assert si_edos.plot_dos_idos(show=False)
            assert si_edos.plot_up_minus_down(show=False)
            assert si_ebands_kmesh.plot_with_edos(edos=si_edos, klabels=klabels, show=False)

            vrange, crange = range(0, 4), range(4, 5)
            assert si_ebands_kmesh.plot_ejdosvc(vrange, crange, cumulative=False, show=False)
            assert si_ebands_kmesh.plot_ejdosvc(vrange, crange, cumulative=True, show=False)
            if self.has_seaborn():
                assert si_ebands_kmesh.boxplot(swarm=True, show=False)

        if self.has_ipywidgets():
            assert si_ebands_kmesh.ipw_edos_widget()

        # Test Abipy --> Pymatgen converter.
        #pmg_bands_kpath = si_ebands_kpath.to_pymatgen()
        pmg_bands_kmesh = si_ebands_kmesh.to_pymatgen()

        # Test JDOS methods.
        spin = 0
        conduction = [4,]
        for v in range(1, 5):
            valence = range(0, v)
            jdos = si_ebands_kmesh.get_ejdos(spin, valence, conduction)
            intg = jdos.integral()[-1][-1]
            self.assert_almost_equal(intg, len(conduction) * len(valence))

        self.serialize_with_pickle(jdos, protocols=[-1])

        si_ebands_kpath = ElectronBands.from_file(abidata.ref_file("si_nscf_GSR.nc"))

        diffs = si_ebands_kpath.statdiff(si_ebands_kpath)
        assert diffs is not None
        str(diffs)

        # TODO: More tests
        # Test abipy-->pymatgen converter
        pmg_bands = si_ebands_kpath.to_pymatgen()

        # Test the detection of denerate states.
        degs = si_ebands_kpath.degeneracies(spin=0, kpoint=[0, 0, 0], bands_range=range(8))
        ref_degbands = [[0], [1, 2, 3], [4, 5, 6], [7]]
        for i, (e, deg_bands) in enumerate(degs):
            self.assertEqual(deg_bands, ref_degbands[i])

        # Test Electron
        e1 = si_ebands_kpath._electron_state(spin=0, kpoint=[0, 0, 0], band=0)
        repr(e1); str(e1)
        e1_copy = e1.copy()
        assert isinstance(e1.as_dict(), dict)
        assert isinstance(e1.to_strdict(), dict)
        assert e1.spin == 0
        assert e1.skb[0] == 0
        str(e1.tips)

        # JDOS requires a homogeneous sampling.
        with self.assertRaises(ValueError):
            si_ebands_kpath.get_ejdos(spin, 0, 4)

    def test_ebands_skw_interpolation(self):
        if sys.version[0:3] >= '3.4':
            raise unittest.SkipTest(
                "SKW interpolation is not tested if Python version >= 3.4 (linalg.solve portability issue)"
             )

        # TODO: interpolation with nsppol 2
        si_ebands_kmesh = ElectronBands.from_file(abidata.ref_file("si_scf_GSR.nc"))

        # Test interpolation.
        vertices_names = [((0.0, 0.0, 0.0), "G"), ((0.5, 0.5, 0.0), "M")]
        r = si_ebands_kmesh.interpolate(lpratio=10, vertices_names=vertices_names,
                                        kmesh=[8, 8, 8], verbose=1)
        assert r.ebands_kpath is not None
        assert r.ebands_kpath.kpoints.is_path
        assert not r.ebands_kpath.kpoints.is_ibz
        mpdivs, shifts = r.ebands_kpath.kpoints.mpdivs_shifts
        assert mpdivs is None and shifts is None

        assert r.ebands_kmesh is not None
        assert r.ebands_kmesh.kpoints.is_ibz
        assert not r.ebands_kmesh.kpoints.is_path
        assert r.ebands_kmesh.kpoints.ksampling is not None
        assert r.ebands_kmesh.kpoints.is_mpmesh
        mpdivs, shifts = r.ebands_kmesh.kpoints.mpdivs_shifts
        self.assert_equal(mpdivs, [8, 8, 8])
        self.assert_equal(shifts.flatten(), [0, 0, 0])

        # Export it in BXSF format.
        r.ebands_kmesh.to_bxsf(self.get_tmpname(text=True))

    def test_derivatives(self):
        """Testing computation of effective masses."""
        ebands = ElectronBands.from_file(abidata.ref_file("si_nscf_GSR.nc"))

        # Hack eigens to simulate free-electron bands. This will produce all(effective masses == 1)
        new_eigens = np.empty(ebands.shape)
        branch = 0.5 * units.Ha_to_eV * np.array([(k.norm * units.bohr_to_ang)**2 for k in ebands.kpoints])
        for spin in ebands.spins:
            for band in range(ebands.mband):
                new_eigens[spin, :, band] = branch
        ebands._eigens = new_eigens

        effm_lines = ebands.effective_masses(spin=0, band=0, acc=2)

        # Flatten structure (.flatten does not work in this case)
        values = []
        for arr in effm_lines:
            values.extend(arr)
        self.assertArrayAlmostEqual(np.array(values), 1.0)

    def test_to_bxsf(self):
        """Testing Fermi surface exporter."""
        from abipy.abilab import abiopen
        with abiopen(abidata.ref_file("mgb2_kmesh181818_FATBANDS.nc")) as fbnc_kmesh:
            fbnc_kmesh.ebands.to_bxsf(self.get_tmpname(text=True))

    def test_frame_from_ebands(self):
        """Testing frame_from_ebands."""
        gsr_kmesh = abidata.ref_file("si_scf_GSR.nc")
        si_ebands_kmesh = ElectronBands.as_ebands(gsr_kmesh)
        gsr_nscf_path = abidata.ref_file("si_nscf_GSR.nc")
        index = ["foo", "bar", "hello"]
        df = frame_from_ebands([gsr_kmesh, si_ebands_kmesh, gsr_nscf_path], index=index, with_spglib=True)
        #print(df)
        assert all(f == "Si2" for f in df["formula"])
        assert all(num == 227 for num in df["abispg_num"])
        assert all(df["spglib_num"] == df["abispg_num"])


class ElectronBandsPlotterTest(AbipyTest):

    def test_api(self):
        """Test ElelectronBandsPlotter API."""
        plotter = ElectronBandsPlotter(key_ebands=[("Si1", abidata.ref_file("si_scf_GSR.nc"))])
        plotter.add_ebands("Si2", abidata.ref_file("si_scf_GSR.nc"))
        repr(plotter); str(plotter)

        assert len(plotter.ebands_list) == 2
        assert len(plotter.edoses_list) == 0
        with self.assertRaises(ValueError):
            plotter.add_ebands("Si2", abidata.ref_file("si_scf_GSR.nc"))

        print(plotter.bands_statdiff())
        df = plotter.get_ebands_frame()
        assert df is not None

        if self.has_matplotlib():
            assert plotter.combiplot(title="Silicon band structure", show=False)
            if self.has_seaborn():
                plotter.combiboxplot(title="Silicon band structure", swarm=True, show=False)
            assert plotter.gridplot(title="Silicon band structure", show=False)
            assert plotter.boxplot(title="Silicon band structure", swarm=True, show=False)
            assert plotter.animate(show=False)

        if self.has_ipywidgets():
            assert plotter.ipw_select_plot() is not None

        if self.has_nbformat():
            assert plotter.write_notebook(nbpath=self.get_tmpname(text=True))

        pickle_path = self.get_tmpname(text=True)
        plotter.pickle_dump(pickle_path)
        same = ElectronBandsPlotter.pickle_load(pickle_path)
        assert len(same.ebands_dict) == len(plotter.ebands_dict)
        assert list(same.ebands_dict.keys()) == list(plotter.ebands_dict.keys())


class ElectronDosPlotterTest(AbipyTest):

    def test_api(self):
        """Test ElelectronDosPlotter API."""
        gsr_path = abidata.ref_file("si_scf_GSR.nc")
        gs_bands = ElectronBands.from_file(gsr_path)
        si_edos = gs_bands.get_edos()

        plotter = ElectronDosPlotter()
        plotter.add_edos("edos1", si_edos)
        with self.assertRaises(ValueError):
            plotter.add_edos("edos1", si_edos)
        plotter.add_edos("edos2", gsr_path, edos_kwargs=dict(method="gaussian", step=0.2, width=0.4))
        assert len(plotter.edos_list) == 2
        assert not plotter._can_use_basenames_as_labels()

        if self.has_matplotlib():
            assert plotter.combiplot(show=False)
            assert plotter.gridplot(show=False)

        if self.has_ipywidgets():
            assert plotter.ipw_select_plot() is not None

        if self.has_nbformat():
            assert plotter.write_notebook(nbpath=self.get_tmpname(text=True))

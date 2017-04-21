import unittest
import numpy as np
import os
import shutil
import pyfstat


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


class TestWriter(Test):
    label = "Test"

    def test_make_cff(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir)
        Writer.make_cff()
        self.assertTrue(os.path.isfile('./TestData/Test.cff'))

    def test_run_makefakedata(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir)
        Writer.make_cff()
        Writer.run_makefakedata()
        self.assertTrue(os.path.isfile(
            './TestData/H-4800_H1_1800SFT_Test-700000000-8640000.sft'))

    def test_makefakedata_usecached(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir)
        if os.path.isfile(Writer.sftfilepath):
            os.remove(Writer.sftfilepath)
        Writer.run_makefakedata()
        time_first = os.path.getmtime(Writer.sftfilepath)
        Writer.run_makefakedata()
        time_second = os.path.getmtime(Writer.sftfilepath)
        self.assertTrue(time_first == time_second)
        os.system('touch {}'.format(Writer.config_file_name))
        Writer.run_makefakedata()
        time_third = os.path.getmtime(Writer.sftfilepath)
        self.assertFalse(time_first == time_third)


class TestBaseSearchClass(Test):
    def test_shift_matrix(self):
        BSC = pyfstat.BaseSearchClass()
        dT = 10
        a = BSC._shift_matrix(4, dT)
        b = np.array([[1, 2*np.pi*dT, 2*np.pi*dT**2/2.0, 2*np.pi*dT**3/6.0],
                      [0, 1, dT, dT**2/2.0],
                      [0, 0, 1, dT],
                      [0, 0, 0, 1]])
        self.assertTrue(np.array_equal(a, b))

    def test_shift_coefficients(self):
        BSC = pyfstat.BaseSearchClass()
        thetaA = np.array([10., 1e2, 10., 1e2])
        dT = 100

        # Calculate the 'long' way
        thetaB = np.zeros(len(thetaA))
        thetaB[3] = thetaA[3]
        thetaB[2] = thetaA[2] + thetaA[3]*dT
        thetaB[1] = thetaA[1] + thetaA[2]*dT + .5*thetaA[3]*dT**2
        thetaB[0] = thetaA[0] + 2*np.pi*(thetaA[1]*dT + .5*thetaA[2]*dT**2
                                         + thetaA[3]*dT**3 / 6.0)

        self.assertTrue(
            np.array_equal(
                thetaB, BSC._shift_coefficients(thetaA, dT)))

    def test_shift_coefficients_loop(self):
        BSC = pyfstat.BaseSearchClass()
        thetaA = np.array([10., 1e2, 10., 1e2])
        dT = 1e1
        thetaB = BSC._shift_coefficients(thetaA, dT)
        self.assertTrue(
            np.allclose(
                thetaA, BSC._shift_coefficients(thetaB, -dT),
                rtol=1e-9, atol=1e-9))


class TestComputeFstat(Test):
    label = "Test"

    def test_run_computefstatistic_single_point(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir)
        Writer.make_data()
        predicted_FS = Writer.predict_fstat()

        search = pyfstat.ComputeFstat(
            tref=Writer.tref,
            sftfilepath='{}/*{}*sft'.format(Writer.outdir, Writer.label))
        FS = search.run_computefstatistic_single_point(Writer.tstart,
                                                       Writer.tend,
                                                       Writer.F0,
                                                       Writer.F1,
                                                       Writer.F2,
                                                       Writer.Alpha,
                                                       Writer.Delta)
        print predicted_FS, FS
        self.assertTrue(np.abs(predicted_FS-FS)/FS < 0.2)

    def run_computefstatistic_single_point_no_noise(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir, add_noise=False)
        Writer.make_data()
        predicted_FS = Writer.predict_fstat()

        search = pyfstat.ComputeFstat(
            tref=Writer.tref, assumeSqrtSX=1,
            sftfilepath='{}/*{}*sft'.format(Writer.outdir, Writer.label))
        FS = search.run_computefstatistic_single_point(Writer.tstart,
                                                       Writer.tend,
                                                       Writer.F0,
                                                       Writer.F1,
                                                       Writer.F2,
                                                       Writer.Alpha,
                                                       Writer.Delta)
        print predicted_FS, FS
        self.assertTrue(np.abs(predicted_FS-FS)/FS < 0.2)

    def test_injectSources_from_file(self):
        Writer = pyfstat.Writer(self.label, outdir=outdir, add_noise=False)
        Writer.make_cff()
        injectSources = Writer.config_file_name

        search = pyfstat.ComputeFstat(
            tref=Writer.tref, assumeSqrtSX=1, injectSources=injectSources,
            minCoverFreq=28, maxCoverFreq=32, minStartTime=Writer.tstart,
            maxStartTime=Writer.tstart+Writer.duration,
            detectors=Writer.detectors)
        FS = search.run_computefstatistic_single_point(Writer.tstart,
                                                       Writer.tend,
                                                       Writer.F0,
                                                       Writer.F1,
                                                       Writer.F2,
                                                       Writer.Alpha,
                                                       Writer.Delta)
        Writer.make_data()
        predicted_FS = Writer.predict_fstat()
        print predicted_FS, FS
        self.assertTrue(np.abs(predicted_FS-FS)/FS < 0.2)


class TestSemiCoherentGlitchSearch(Test):
    label = "Test"

    def test_compute_nglitch_fstat(self):
        duration = 100*86400
        dtglitch = .5*100*86400
        delta_F0 = 0
        Writer = pyfstat.Writer(self.label, outdir=outdir,
                                duration=duration, dtglitch=dtglitch,
                                delta_F0=delta_F0)

        Writer.make_data()

        search = pyfstat.SemiCoherentGlitchSearch(
            label=self.label, outdir=outdir,
            sftfilepath='{}/*{}*sft'.format(Writer.outdir, Writer.label),
            tref=Writer.tref, minStartTime=Writer.tstart,
            maxStartTime=Writer.tend, nglitch=1)

        FS = search.compute_nglitch_fstat(Writer.F0, Writer.F1, Writer.F2,
                                          Writer.Alpha, Writer.Delta,
                                          Writer.delta_F0, Writer.delta_F1,
                                          search.minStartTime+dtglitch)

        # Compute the predicted semi-coherent glitch Fstat
        minStartTime = Writer.tstart
        maxStartTime = Writer.tend

        Writer.maxStartTime = minStartTime + dtglitch
        FSA = Writer.predict_fstat()

        Writer.tstart = minStartTime + dtglitch
        Writer.tend = maxStartTime
        FSB = Writer.predict_fstat()

        print FSA, FSB
        predicted_FS = (FSA + FSB)

        print(predicted_FS, FS)
        self.assertTrue(np.abs((FS - predicted_FS))/predicted_FS < 0.3)


class TestMCMCSearch(Test):
    label = "Test"

    def test_fully_coherent(self):
        h0 = 5e-24
        sqrtSX = 1e-22
        F0 = 30
        F1 = -1e-10
        F2 = 0
        minStartTime = 700000000
        duration = 100 * 86400
        maxStartTime = minStartTime + duration
        Alpha = 5e-3
        Delta = 1.2
        tref = minStartTime
        delta_F0 = 0
        Writer = pyfstat.Writer(F0=F0, F1=F1, F2=F2, label=self.label,
                                h0=h0, sqrtSX=sqrtSX,
                                outdir=outdir, tstart=minStartTime,
                                Alpha=Alpha, Delta=Delta, tref=tref,
                                duration=duration,
                                delta_F0=delta_F0, Band=4)

        Writer.make_data()
        predicted_FS = Writer.predict_fstat()

        theta = {'F0': {'type': 'norm', 'loc': F0, 'scale': np.abs(1e-9*F0)},
                 'F1': {'type': 'norm', 'loc': F1, 'scale': np.abs(1e-9*F1)},
                 'F2': F2, 'Alpha': Alpha, 'Delta': Delta}

        search = pyfstat.MCMCSearch(
            label=self.label, outdir=outdir, theta_prior=theta, tref=tref,
            sftfilepath='{}/*{}*sft'.format(Writer.outdir, Writer.label),
            minStartTime=minStartTime, maxStartTime=maxStartTime,
            nsteps=[100, 100], nwalkers=100, ntemps=2, log10temperature_min=-1)
        search.setup_convergence_testing()
        search.run(create_plots=False)
        _, FS = search.get_max_twoF()

        print('Predicted twoF is {} while recovered is {}'.format(
                predicted_FS, FS))
        self.assertTrue(
            FS > predicted_FS or np.abs((FS-predicted_FS))/predicted_FS < 0.3)

    def test_multi_stage(self):
        Writer = pyfstat.Writer(F0=10)
        Writer.make_cff()

        theta = {'F0': {'type': 'norm', 'loc': 10, 'scale': 1e-2},
                 'F1': 0, 'F2': 0, 'Alpha': 0, 'Delta': 0}

        search = pyfstat.MCMCSearch(
            label=self.label, outdir=outdir, theta_prior=theta,
            tref=Writer.tref, injectSources=Writer.config_file_name,
            minStartTime=Writer.minStartTime, maxStartTime=Writer.maxStartTime,
            nsteps=[5, 5], nwalkers=20, ntemps=1, detectors='H1',
            minCoverFreq=9, maxCoverFreq=11)
        search.run(create_plots=False)


class TestAuxillaryFunctions(Test):
    nsegs = 10
    minStartTime = 1e9
    maxStartTime = minStartTime + 100 * 86400
    tref = .5*(minStartTime + maxStartTime)
    DeltaOmega = 1e-2
    DeltaFs = [1e-4, 1e-14]
    fiducial_freq = 100
    detector_names = ['H1', 'L1']
    earth_ephem, sun_ephem = pyfstat.helper_functions.set_up_ephemeris_configuration()

    def test_get_V_estimate_sky_F0_F1(self):

        out = pyfstat.optimal_setup_functions.get_V_estimate(
            self.nsegs, self.tref, self.minStartTime, self.maxStartTime,
            self.DeltaOmega, self.DeltaFs, self.fiducial_freq,
            self.detector_names, self.earth_ephem, self.sun_ephem)
        V, Vsky, Vpe = out
        self.assertTrue(V == Vsky * Vpe)
        self.__class__.Vpe_COMPUTED_WITH_SKY = Vpe

    def test_get_V_estimate_F0_F1(self):
        out = pyfstat.optimal_setup_functions.get_V_estimate(
            self.nsegs, self.tref, self.minStartTime, self.maxStartTime,
            self.DeltaOmega, self.DeltaFs, self.fiducial_freq,
            self.detector_names, self.earth_ephem, self.sun_ephem)
        V, Vsky, Vpe = out
        self.assertTrue(V == Vsky * Vpe)
        self.__class__.Vpe_COMPUTED_WITHOUT_SKY = Vpe

    def test_the_equivalence_of_Vpe(self):
        """Tests if the Vpe computed with and without the sky are equal """
        self.assertEqual(self.__class__.Vpe_COMPUTED_WITHOUT_SKY,
                         self.__class__.Vpe_COMPUTED_WITH_SKY)

if __name__ == '__main__':
    outdir = 'TestData'
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    unittest.main()
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)


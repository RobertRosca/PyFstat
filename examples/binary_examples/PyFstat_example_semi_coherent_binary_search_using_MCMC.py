import pyfstat
import numpy as np
import os

label = os.path.splitext(os.path.basename(__file__))[0]
outdir = os.path.join("PyFstat_example_data", label)

# Properties of the GW data
data_parameters = {
    "sqrtSX": 1e-23,
    "tstart": 1000000000,
    "duration": 100 * 86400,
    "detectors": "H1",
}
tend = data_parameters["tstart"] + data_parameters["duration"]
mid_time = 0.5 * (data_parameters["tstart"] + tend)

# Properties of the signal
depth = 0.1
signal_parameters = {
    "F0": 30.0,
    "F1": 0,
    "F2": 0,
    "Alpha": 0.15,
    "Delta": 0.45,
    "tp": mid_time,
    "argp": 0.3,
    "asini": 10.0,
    "ecc": 0.5,
    "period": 45 * 24 * 3600.0,
    "tref": mid_time,
    "h0": data_parameters["sqrtSX"] / depth,
    "cosi": 1.0,
}

data = pyfstat.BinaryModulatedWriter(
    label=label, outdir=outdir, **data_parameters, **signal_parameters
)
data.make_data()

DeltaF0 = 1e-7
DeltaF1 = 1e-13
VF0 = (np.pi * data_parameters["duration"] * DeltaF0) ** 2 / 3.0
VF1 = (np.pi * data_parameters["duration"] ** 2 * DeltaF1) ** 2 * 4 / 45.0
print("\nV={:1.2e}, VF0={:1.2e}, VF1={:1.2e}\n".format(VF0 * VF1, VF0, VF1))

theta_prior = {
    "F0": signal_parameters["F0"],
    "F1": signal_parameters["F1"],
    "F2": signal_parameters["F2"],
    "Alpha": {
        "type": "unif",
        "lower": signal_parameters["Alpha"] - 0.01,
        "upper": signal_parameters["Alpha"] + 0.01,
    },
    "Delta": {
        "type": "unif",
        "lower": signal_parameters["Delta"] - 0.01,
        "upper": signal_parameters["Delta"] + 0.01,
    },
    "asini": {"type": "unif", "lower": 9.9, "upper": 10.1},
    "period": {
        "type": "unif",
        "lower": 44.99 * 24 * 3600.0,
        "upper": 45.01 * 24 * 3600.0,
    },
    "ecc": {
        "type": "unif",
        "lower": signal_parameters["ecc"] - 5e-2,
        "upper": signal_parameters["ecc"] + 5e-2,
    },
    "argp": {
        "type": "unif",
        "lower": signal_parameters["argp"] - np.pi / 2,
        "upper": signal_parameters["argp"] + np.pi / 2,
    },
    "tp": {
        "type": "unif",
        "lower": mid_time - signal_parameters["period"] / 2.0,
        "upper": mid_time + signal_parameters["period"] / 2.0,
    },
}

ntemps = 3
log10beta_min = -1
nwalkers = 150
nsteps = [100, 200]

mcmc = pyfstat.MCMCSemiCoherentSearch(
    label=label,
    outdir=outdir,
    nsegs=10,
    sftfilepattern=os.path.join(outdir, "*{}*sft".format(label)),
    theta_prior=theta_prior,
    tref=signal_parameters["tref"],
    minStartTime=data_parameters["tstart"],
    maxStartTime=tend,
    nsteps=nsteps,
    nwalkers=nwalkers,
    ntemps=ntemps,
    log10beta_min=log10beta_min,
    binary=True,
)

mcmc.run(
    plot_walkers=True,
    walker_plot_args={"plot_det_stat": True, "injection_parameters": signal_parameters},
)
mcmc.plot_corner(add_prior=True, truths=signal_parameters)
mcmc.plot_prior_posterior(injection_parameters=signal_parameters)
mcmc.print_summary()

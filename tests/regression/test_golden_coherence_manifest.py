"""Regression tests: rgcs_core.coherence port vs the golden coherence
manifest (experiments/sample_data/golden_coherence/manifest.json).

The manifest is the NORMATIVE source of expected values; nothing here is
hard-coded from the test-matrix tables (docs/COHERENCE_TEST_MATRIX.md
header rule 2). Tolerance semantics: atol / rtol / min / max / exact.
"""

from __future__ import annotations

import csv
import math
import os

import numpy as np
import pytest
from scipy import stats

from rgcs_core.coherence import (coherence_series, noise_baseline_theory,
                                 band_power_fraction, phase_linearity,
                                 instantaneous_frequency,
                                 coherence_onset_time, coherence_decay_time,
                                 rayleigh_test, circular_mean,
                                 circular_variance, circular_resultant,
                                 phase_locking_value, instantaneous_phase,
                                 spatial_phase_anisotropy,
                                 model_comparison,
                                 threshold_detect_bootstrap)

# ---------------------------------------------------------------- helpers


def load_rows(path: str) -> list[list[str]]:
    with open(path) as fh:
        reader = csv.reader(fh)
        header = next(reader)
        return header, list(reader)


def check(entry: dict, got):
    """Apply the manifest's tolerance semantics to a recomputed value."""
    expected = entry["value"]
    if entry.get("exact"):
        assert got == expected, f"exact mismatch: {got!r} != {expected!r}"
        return
    if "atol" in entry:
        assert abs(got - expected) <= entry["atol"], \
            f"|{got} - {expected}| > atol {entry['atol']}"
    if "rtol" in entry:
        assert abs(got - expected) <= entry["rtol"] * abs(expected), \
            f"|{got} - {expected}| > rtol {entry['rtol']}*|{expected}|"
    if "min" in entry:
        assert got >= entry["min"], f"{got} < min {entry['min']}"
    if "max" in entry:
        assert got <= entry["max"], f"{got} > max {entry['max']}"


@pytest.fixture(scope="module")
def params(manifest):
    return {"fs": manifest["fs_hz"], "f0": manifest["f0_hz"],
            "w": manifest["coherence_window_s"],
            "hop": manifest["coherence_hop_s"]}


def demod_first_window_phase(z: np.ndarray, fs: float, f0: float,
                             window_s: float) -> float:
    w0 = z[:int(window_s * fs)]
    t = np.arange(w0.size) / fs
    ref = np.exp(1j * 2 * np.pi * f0 * t)
    return float(np.angle(np.sum(w0 * np.conj(ref))))


# --------------------------------------------------------------- case (a)

@pytest.fixture(scope="module")
def case_a(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_a_white_noise"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    z = np.array([float(r[1]) + 1j * float(r[2]) for r in rows])
    tc, c = coherence_series(z, params["fs"], params["w"], params["hop"])
    nwin = int(round(params["w"] * params["fs"]))
    return {"entry": entry, "z": z, "tc": tc, "C": c, "nwin": nwin,
            "p": params}


def test_case_a_coherence_mean_at_baseline(case_a):
    check(case_a["entry"]["expected"]["coherence_mean"],
          float(np.mean(case_a["C"])))


def test_case_a_coherence_never_high(case_a):
    check(case_a["entry"]["expected"]["coherence_max"],
          float(np.max(case_a["C"])))


def test_case_a_baseline_formula(case_a):
    baseline = noise_baseline_theory(case_a["nwin"])
    check(case_a["entry"]["expected"]["baseline_theory"], baseline)
    # atol comparison vs the MEASURED mean (test-matrix wording).
    assert abs(float(np.mean(case_a["C"])) - baseline) <= 0.03


def test_case_a_occupancy_flat(case_a):
    got = band_power_fraction(case_a["z"], case_a["p"]["fs"],
                              case_a["p"]["f0"], 500.0)
    check(case_a["entry"]["expected"]["mode_occupancy_5kHz_500Hz"], got)


def test_case_a_phase_linearity_low(case_a):
    check(case_a["entry"]["expected"]["phase_linearity"],
          phase_linearity(case_a["z"]))


# --------------------------------------------------------------- case (b)

@pytest.fixture(scope="module")
def case_b(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_b_pure_sinusoid"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    z = np.array([float(r[1]) + 1j * float(r[2]) for r in rows])
    tc, c = coherence_series(z, params["fs"], params["w"], params["hop"])
    return {"entry": entry, "z": z, "C": c, "p": params}


def test_case_b_coherence_exactly_one(case_b):
    # CSV stores 9 significant digits, so allow quantization above the
    # manifest's 1e-6 float tolerance on the regenerated signal.
    got = float(np.min(case_b["C"]))
    assert abs(got - case_b["entry"]["expected"]["coherence_min"]["value"]) \
        <= 1e-5


def test_case_b_phase_linearity_one(case_b):
    got = phase_linearity(case_b["z"])
    assert abs(got - case_b["entry"]["expected"]["phase_linearity"]["value"]) \
        <= 1e-5


def test_case_b_instantaneous_frequency(case_b):
    f = instantaneous_frequency(case_b["z"], case_b["p"]["fs"])
    check(case_b["entry"]["expected"]["inst_freq_mean_hz"],
          float(np.mean(f[10:-10])))


def test_case_b_occupancy_full(case_b):
    got = band_power_fraction(case_b["z"], case_b["p"]["fs"],
                              case_b["p"]["f0"], 500.0)
    check(case_b["entry"]["expected"]["mode_occupancy_5kHz_500Hz"], got)


# --------------------------------------------------------------- case (c)

@pytest.fixture(scope="module")
def case_c(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_c_decaying_sinusoid"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    z = np.array([float(r[1]) + 1j * float(r[2]) for r in rows])
    fs, w, hop = params["fs"], params["w"], params["hop"]
    prm = entry["params"]
    t = np.arange(z.size) / fs
    t_on, tau_amp = prm["t_on_s"], prm["tau_amp_s"]
    amp0, sigma_n = prm["amp0"], prm["noise_sigma"]
    env = np.where(t >= t_on, amp0 * np.exp(-(t - t_on) / tau_amp), 0.0)
    tc, c = coherence_series(z, fs, w, hop)
    nwin = int(round(w * fs))
    baseline = noise_baseline_theory(nwin)
    # Mirror the generator's envelope-model-comparison procedure exactly.
    amp_est = np.array([float(np.mean(np.abs(
        z[int((x - w / 2) * fs):int((x + w / 2) * fs)]))) for x in tc])
    amp_corr = amp_est - sigma_n * math.sqrt(math.pi) / 2.0
    sel = (tc >= t_on + w) & (amp_corr > 3.0 * sigma_n)
    mc = model_comparison(tc[sel] - (t_on + w), amp_corr[sel])
    return {"entry": entry, "z": z, "t": t, "env": env, "tc": tc, "C": c,
            "baseline": baseline, "mc": mc, "prm": prm, "p": params}


def test_case_c_coherence_high(case_c):
    check(case_c["entry"]["expected"]["coherence_max"],
          float(np.max(case_c["C"])))


def test_case_c_coherence_survives_amplitude_fall(case_c):
    i = int(np.argmin(np.abs(case_c["tc"] - 0.010)))
    check(case_c["entry"]["expected"]["coherence_at_10ms"],
          float(case_c["C"][i]))


def test_case_c_onset_time(case_c):
    onset = coherence_onset_time(case_c["tc"], case_c["C"], threshold=0.5)
    check(case_c["entry"]["expected"]["onset_time_s"], onset)


def test_case_c_coherence_decay_tau(case_c):
    tau = coherence_decay_time(case_c["tc"], case_c["C"],
                               case_c["baseline"])
    check(case_c["entry"]["expected"]["coherence_decay_tau_s"], tau)


def test_case_c_coherence_below_amplitude_floor(case_c):
    fs = case_c["p"]["fs"]
    idx = np.where(case_c["env"][(case_c["tc"] * fs).astype(int)]
                   < case_c["prm"]["noise_sigma"])[0]
    got = float(np.max(case_c["C"][idx]))
    check(case_c["entry"]["expected"]["coherence_below_amp_floor"], got)
    assert got > 3.0 * case_c["baseline"]        # KOS-10 property


def test_case_c_envelope_model_selection(case_c):
    check(case_c["entry"]["expected"]["envelope_best_model"],
          case_c["mc"]["best_by_AIC"])


def test_case_c_exp_beats_power(case_c):
    got = case_c["mc"]["exponential"]["AIC"] \
        - case_c["mc"]["power_law"]["AIC"]
    check(case_c["entry"]["expected"]["aic_exp_minus_power"], got)


def test_case_c_exp_crushes_nochange(case_c):
    got = case_c["mc"]["exponential"]["AIC"] \
        - case_c["mc"]["no_change"]["AIC"]
    check(case_c["entry"]["expected"]["aic_exp_minus_nochange"], got)


def test_case_c_envelope_tau(case_c):
    check(case_c["entry"]["expected"]["envelope_fit_tau_s"],
          case_c["mc"]["exponential"]["params"]["tau_s"])


# --------------------------------------------------------------- case (d)

@pytest.fixture(scope="module")
def case_d(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_d_random_phase_runs"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    fs, f0, w, hop = (params["fs"], params["f0"], params["w"],
                      params["hop"])
    runs: dict[int, list[complex]] = {}
    for r in rows:
        runs.setdefault(int(r[0]), []).append(float(r[2]) + 1j * float(r[3]))
    per_run_c, per_run_pl, init_phase = [], [], []
    for rid in sorted(runs):
        z = np.array(runs[rid])
        _, c = coherence_series(z, fs, w, hop)
        per_run_c.append(float(np.mean(c)))
        per_run_pl.append(phase_linearity(z))
        init_phase.append(demod_first_window_phase(z, fs, f0, w))
    return {"entry": entry, "per_run_C": np.array(per_run_c),
            "per_run_pl": np.array(per_run_pl),
            "init_phase": np.array(init_phase)}


def test_case_d_per_run_coherence_high(case_d):
    check(case_d["entry"]["expected"]["per_run_coherence_mean"],
          float(np.mean(case_d["per_run_C"])))


def test_case_d_per_run_phase_stable(case_d):
    check(case_d["entry"]["expected"]["per_run_phase_linearity_min"],
          float(np.min(case_d["per_run_pl"])))


def test_case_d_ensemble_resultant_small(case_d):
    check(case_d["entry"]["expected"]["ensemble_Rbar"],
          circular_resultant(case_d["init_phase"]))


def test_case_d_rayleigh_does_not_reject(case_d):
    p = rayleigh_test(case_d["init_phase"])["p"]
    check(case_d["entry"]["expected"]["rayleigh_p"], p)


def test_case_d_circular_variance_high(case_d):
    check(case_d["entry"]["expected"]["circular_variance"],
          circular_variance(case_d["init_phase"]))


# --------------------------------------------------------------- case (e)

@pytest.fixture(scope="module")
def case_e(golden_dir, manifest):
    entry = manifest["datasets"]["case_e_coupled_oscillators"]
    header, rows = load_rows(os.path.join(golden_dir, entry["summary_file"]))
    k_grid = np.array([float(r[0]) for r in rows])
    plv = np.array([[float(v) for v in r[1:]] for r in rows])
    return {"entry": entry, "K": k_grid, "plv": plv,
            "master_seed": manifest["master_seed"]}


def test_case_e_unlocked_below_threshold(case_e):
    check(case_e["entry"]["expected"]["plv_at_K0_mean"],
          float(case_e["plv"][0].mean()))


def test_case_e_locked_above_threshold(case_e):
    check(case_e["entry"]["expected"]["plv_at_Kmax_mean"],
          float(case_e["plv"][-1].mean()))


def test_case_e_plv_monotone_in_K(case_e):
    rho = stats.spearmanr(case_e["K"],
                          case_e["plv"].mean(axis=1)).statistic
    check(case_e["entry"]["expected"]["plv_monotone_spearman_min"],
          float(rho))


def test_case_e_threshold_detection(case_e):
    thr = threshold_detect_bootstrap(case_e["K"], case_e["plv"],
                                     n_boot=500,
                                     seed=case_e["master_seed"] + 55)
    check(case_e["entry"]["expected"]["threshold_K"], thr["threshold"])


def test_case_e_threshold_bootstrap_ci(case_e):
    # Bootstrap seed = MASTER_SEED + 55 (binding handoff requirement).
    thr = threshold_detect_bootstrap(case_e["K"], case_e["plv"],
                                     n_boot=500,
                                     seed=case_e["master_seed"] + 55)
    lo, hi = case_e["entry"]["expected"]["threshold_ci"]["value"]
    assert abs(thr["ci_lo"] - lo) <= 5.0
    assert abs(thr["ci_hi"] - hi) <= 5.0
    assert thr["ci_lo"] <= thr["threshold"] <= thr["ci_hi"]


# --------------------------------------------------------------- case (f)

@pytest.fixture(scope="module")
def case_f(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_f_pump_leakage"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    fs, f0, w, hop = (params["fs"], params["f0"], params["w"],
                      params["hop"])
    runs: dict[tuple[str, int], list[complex]] = {}
    for r in rows:
        runs.setdefault((r[0], int(r[1])), []).append(
            float(r[3]) + 1j * float(r[4]))
    stats_: dict[str, dict[str, list[float]]] = {
        "sample": {"C": [], "ph": []}, "control": {"C": [], "ph": []}}
    for (cond, _rid), zs in sorted(runs.items()):
        z = np.array(zs)
        _, c = coherence_series(z, fs, w, hop)
        stats_[cond]["C"].append(float(np.mean(c)))
        stats_[cond]["ph"].append(demod_first_window_phase(z, fs, f0, w))
    return {"entry": entry, "stats": stats_}


def test_case_f_false_coherence_is_high(case_f):
    check(case_f["entry"]["expected"]["sample_coherence_mean"],
          float(np.mean(case_f["stats"]["sample"]["C"])))


def test_case_f_control_coherence_equal(case_f):
    check(case_f["entry"]["expected"]["control_coherence_mean"],
          float(np.mean(case_f["stats"]["control"]["C"])))


def test_case_f_control_subtraction_nulls_effect(case_f):
    got = (float(np.mean(case_f["stats"]["sample"]["C"]))
           - float(np.mean(case_f["stats"]["control"]["C"])))
    check(case_f["entry"]["expected"]
          ["coherence_excess_sample_minus_control"], got)


def test_case_f_rayleigh_rejects_imprinted_phase(case_f):
    p = rayleigh_test(np.array(case_f["stats"]["sample"]["ph"]))["p"]
    check(case_f["entry"]["expected"]["rayleigh_p_sample"], p)


def test_case_f_ensemble_resultant_near_one(case_f):
    check(case_f["entry"]["expected"]["ensemble_Rbar_sample"],
          circular_resultant(np.array(case_f["stats"]["sample"]["ph"])))


def test_case_f_phase_clusters_at_pump(case_f):
    check(case_f["entry"]["expected"]["ensemble_phase_vs_pump_rad"],
          circular_mean(np.array(case_f["stats"]["sample"]["ph"])))


# --------------------------------------------------------------- case (g)

@pytest.fixture(scope="module")
def case_g(golden_dir, manifest, params):
    entry = manifest["datasets"]["case_g_sensor_geometry"]
    _, rows = load_rows(os.path.join(golden_dir, entry["file"]))
    fs, w, hop = params["fs"], params["w"], params["hop"]
    conds: dict[str, dict[str, list[complex]]] = {}
    for r in rows:
        d = conds.setdefault(r[0], {"p1": [], "p2": [], "p3": [],
                                    "wide": []})
        d["p1"].append(float(r[2]) + 1j * float(r[3]))
        d["p2"].append(float(r[4]) + 1j * float(r[5]))
        d["p3"].append(float(r[6]) + 1j * float(r[7]))
        d["wide"].append(float(r[8]) + 1j * float(r[9]))
    results = {}
    for cond, d in conds.items():
        chans = [np.array(d[k]) for k in ("p1", "p2", "p3")]
        wide = np.array(d["wide"])
        _, cw = coherence_series(wide, fs, w, hop)
        cp = [float(np.mean(coherence_series(c, fs, w, hop)[1]))
              for c in chans]
        phases = np.vstack([instantaneous_phase(c) for c in chans])
        aniso = spatial_phase_anisotropy(phases, fs, w, hop)
        results[cond] = {"C_wide_mean": float(np.mean(cw)),
                         "C_point_mean": float(np.mean(cp)),
                         "aniso_scalar": aniso["scalar_rad2_per_s2"]}
    return {"entry": entry, "r": results}


def test_case_g_long_point_coherent(case_g):
    check(case_g["entry"]["expected"]["long_point_coherence"],
          case_g["r"]["coherent_long"]["C_point_mean"])


def test_case_g_long_wide_coherent(case_g):
    check(case_g["entry"]["expected"]["long_wide_coherence"],
          case_g["r"]["coherent_long"]["C_wide_mean"])


def test_case_g_short_point_coherent(case_g):
    check(case_g["entry"]["expected"]["short_point_coherence"],
          case_g["r"]["coherent_short"]["C_point_mean"])


def test_case_g_short_wide_filtered(case_g):
    check(case_g["entry"]["expected"]["short_wide_coherence"],
          case_g["r"]["coherent_short"]["C_wide_mean"])


def test_case_g_anisotropy_small_when_common(case_g):
    check(case_g["entry"]["expected"]["aniso_scalar_coherent_long"],
          case_g["r"]["coherent_long"]["aniso_scalar"])


def test_case_g_anisotropy_matches_detuning(case_g):
    check(case_g["entry"]["expected"]["aniso_scalar_detuned"],
          case_g["r"]["detuned_channels"]["aniso_scalar"])


def test_case_g_anisotropy_contrast(case_g):
    got = (case_g["r"]["detuned_channels"]["aniso_scalar"]
           / case_g["r"]["coherent_long"]["aniso_scalar"])
    check(case_g["entry"]["expected"]["aniso_ratio_detuned_over_long"], got)


# ------------------------------------------------------- cross-cutting

def test_forbidden_vocabulary_in_manifest_context(manifest):
    """The naming gate applied to this pipeline's own outputs: the port's
    anisotropy result dicts must use the approved name."""
    from rgcs_core.provenance import contains_forbidden_vocabulary
    fs = 100_000.0
    t = np.arange(400) / fs
    phases = np.vstack([2 * np.pi * 5000.0 * t] * 3)
    out = spatial_phase_anisotropy(phases, fs)
    assert not contains_forbidden_vocabulary(str(out))
    assert "scalar_rad2_per_s2" in out

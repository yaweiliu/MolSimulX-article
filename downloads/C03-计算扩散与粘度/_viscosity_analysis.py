"""Green–Kubo viscosity from LAMMPS ``fix ave/correlate`` output."""

from __future__ import annotations

__version__ = "1.0.0"
__date__ = "2026-07-26"

from pathlib import Path

import numpy as np


def read_ave_correlate_last(filename="result_viscosity_correlate.dat"):
    """Read the last block of a LAMMPS ``ave/correlate`` file."""
    path = Path(filename)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    headers = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) == 2:
            try:
                headers.append((i, int(parts[0]), int(parts[1])))
            except ValueError:
                pass
    if not headers:
        raise ValueError(f"No ave/correlate block headers in {path}")

    start, timestep, nwindow = headers[-1]
    rows = []
    for raw in lines[start + 1 :]:
        s = raw.strip()
        if not s or s.startswith("#"):
            break
        parts = s.split()
        if len(parts) == 2 or len(parts) < 4:
            break
        rows.append([float(x) for x in parts])
    if not rows:
        raise ValueError(f"Empty last correlate block in {path}")

    arr = np.asarray(rows, dtype=float)
    return {
        "timestep": timestep,
        "nwindow": nwindow,
        "index": arr[:, 0],
        "timedelta": arr[:, 1],
        "ncount": arr[:, 2],
        "corr": arr[:, 3:],
    }


def integrate_gk_viscosity(
    correlate,
    *,
    volume_A3,
    temperature_K=300.0,
    nevery=5,
    dt_fs=1.0,
    t_cut_fs=None,
    corr_columns=None,
):
    """Trapezoidal GK integral → η [Pa·s / cP] (LAMMPS ``real`` units).

    ``corr_columns`` selects which autocorrelation columns to average
    (default: all).
    """
    corr = np.asarray(correlate["corr"], dtype=float)
    if corr_columns is not None:
        corr = corr[:, corr_columns]
    times_fs = np.asarray(correlate["timedelta"], dtype=float) * dt_fs

    if t_cut_fs is not None:
        mask = times_fs <= t_cut_fs
        times_fs = times_fs[mask]
        corr = corr[mask]

    corr_mean = corr.mean(axis=1)
    kB = 1.380649e-23
    atm2Pa = 101325.0
    convert = atm2Pa * atm2Pa * 1.0e-30 * 1.0e-15
    scale = float(volume_A3) * convert / (kB * float(temperature_K))

    running = np.zeros_like(corr_mean)
    for i in range(1, len(corr_mean)):
        running[i] = running[i - 1] + 0.5 * (corr_mean[i] + corr_mean[i - 1]) * (
            times_fs[i] - times_fs[i - 1]
        )
    eta_pas = running * scale
    eta_cp = eta_pas * 1000.0
    eta_pas_lmp = float(np.trapezoid(corr_mean, dx=1.0)) * scale * nevery * dt_fs

    return {
        "times_fs": times_fs,
        "corr_mean": corr_mean,
        "corr": corr,
        "running_eta_Pas": eta_pas,
        "running_eta_cP": eta_cp,
        "eta_Pas": float(eta_pas[-1]),
        "eta_cP": float(eta_cp[-1]),
        "eta_Pas_lammps_trap": eta_pas_lmp,
        "eta_cP_lammps_trap": eta_pas_lmp * 1000.0,
    }

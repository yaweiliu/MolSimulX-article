"""Translational self-diffusion (Einstein MSD) via MDAnalysis.

Trajectory must be **unwrapped** (e.g. LAMMPS ``xsu ysu zsu``).

- ``msd_from_selection`` — atom selection + ``EinsteinMSD``
- ``msd_from_com`` — residue/fragment COM + ``tidynamics`` FFT
- ``translational_diffusion`` — dispatch ``mode='selection'|'com'``

Use ``n_frames=N`` (or ``stop``) to analyse only the first N frames for testing.
"""

from __future__ import annotations

__version__ = "1.1.0"
__date__ = "2026-07-26"

import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis.msd import EinsteinMSD

try:
    import tidynamics
except ImportError as exc:  # pragma: no cover
    tidynamics = None
    _TIDYNAMICS_ERROR = exc
else:
    _TIDYNAMICS_ERROR = None


def _resolve_frame_slice(
    start: int | None,
    stop: int | None,
    step: int,
    n_frames: int | None,
) -> tuple[int | None, int | None, int]:
    """Apply optional ``n_frames`` (first N frames from ``start``) for testing."""
    start_i = 0 if start is None else int(start)
    if n_frames is not None:
        n = int(n_frames)
        if n <= 0:
            raise ValueError(f"n_frames must be positive; got {n_frames!r}")
        stop_i = start_i + n
        if stop is not None:
            stop_i = min(stop_i, int(stop))
        return start_i, stop_i, int(step)
    return start, stop, int(step)


def fit_msd_diffusion(
    times_ps: np.ndarray,
    msd_A2: np.ndarray,
    *,
    t_min_ps: float = 10.0,
    t_max_ps: float | None = None,
    ndim: int = 3,
) -> tuple[float, float, slice]:
    """Fit MSD = (2 * ndim) * D * t → D [Å²/ps] and [m²/s]."""
    if ndim not in (1, 2, 3):
        raise ValueError(f"ndim must be 1, 2, or 3; got {ndim}")
    if t_max_ps is None:
        t_max_ps = 0.4 * float(times_ps[-1])
    mask = (times_ps >= t_min_ps) & (times_ps <= t_max_ps)
    if int(mask.sum()) < 3:
        raise ValueError(
            f"Not enough MSD points in [{t_min_ps}, {t_max_ps}] ps "
            f"(have {int(mask.sum())})"
        )
    t = times_ps[mask]
    y = msd_A2[mask]
    slope, _ = np.polyfit(t, y, 1)
    d_a2_ps = float(slope / (2.0 * ndim))
    d_m2_s = d_a2_ps * 1.0e-20 / 1.0e-12
    idx = np.where(mask)[0]
    return d_a2_ps, d_m2_s, slice(int(idx[0]), int(idx[-1]) + 1)


def _pack_result(
    times_ps, msd_A2, *, method, t_min_ps, t_max_ps, ndim=3, extra=None
):
    d_a2_ps, d_m2_s, fit_sl = fit_msd_diffusion(
        times_ps, msd_A2, t_min_ps=t_min_ps, t_max_ps=t_max_ps, ndim=ndim
    )
    out = {
        "method": method,
        "times_ps": times_ps,
        "msd_A2": msd_A2,
        "n_frames_used": int(len(times_ps)),
        "D_A2_ps": d_a2_ps,
        "D_m2_s": d_m2_s,
        "D_1e5_cm2_s": d_m2_s * 1.0e9,
        "fit_slice": fit_sl,
        "ndim": ndim,
    }
    if extra:
        out.update(extra)
    return out


def msd_from_selection(
    u: mda.Universe,
    *,
    select: str = "all",
    dt_fs: float = 500.0,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
    fft: bool = True,
    msd_type: str = "xyz",
    t_min_ps: float = 10.0,
    t_max_ps: float | None = None,
    ndim: int | None = None,
) -> dict:
    """Einstein MSD for an MDAnalysis atom selection."""
    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)
    if ndim is None:
        ndim = len(msd_type)
    analysis = EinsteinMSD(u, select=select, msd_type=msd_type, fft=fft)
    analysis.run(start=start, stop=stop, step=step)
    msd = np.asarray(analysis.results.timeseries, dtype=float)
    times_ps = np.arange(len(msd), dtype=float) * (dt_fs * step) / 1000.0
    return _pack_result(
        times_ps,
        msd,
        method="selection",
        t_min_ps=t_min_ps,
        t_max_ps=t_max_ps,
        ndim=ndim,
        extra={
            "select": select,
            "n_particles": u.select_atoms(select).n_atoms,
            "analysis": analysis,
        },
    )


def msd_from_com(
    u: mda.Universe,
    *,
    select: str = "all",
    compound: str = "residues",
    dt_fs: float = 500.0,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
    unwrap: bool = True,
    t_min_ps: float = 10.0,
    t_max_ps: float | None = None,
    ndim: int = 3,
) -> dict:
    """COM MSD (``tidynamics`` FFT) for residues / fragments."""
    if tidynamics is None:
        raise ImportError(
            "tidynamics required for COM MSD "
            "(same as MDAnalysis EinsteinMSD fft=True)"
        ) from _TIDYNAMICS_ERROR

    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)
    ag = u.select_atoms(select)
    if ag.n_atoms == 0:
        raise ValueError(f"No atoms matched select={select!r}")

    frames = []
    for _ts in u.trajectory[start:stop:step]:
        com = ag.center_of_mass(compound=compound, unwrap=unwrap)
        frames.append(np.asarray(com, dtype=float))
    if not frames:
        raise ValueError("No frames selected for COM MSD")
    positions = np.stack(frames, axis=0)
    if positions.ndim == 2:
        positions = positions[:, None, :]

    positions = positions - positions.mean(axis=1, keepdims=True)
    n_fr, n_part, _ = positions.shape
    acc = np.zeros(n_fr, dtype=float)
    for i in range(n_part):
        acc += tidynamics.msd(positions[:, i, :])
    msd = acc / n_part

    times_ps = np.arange(len(msd), dtype=float) * (dt_fs * step) / 1000.0
    return _pack_result(
        times_ps,
        msd,
        method="com",
        t_min_ps=t_min_ps,
        t_max_ps=t_max_ps,
        ndim=ndim,
        extra={
            "select": select,
            "compound": compound,
            "n_particles": n_part,
            "com": positions,
        },
    )


def translational_diffusion(
    u: mda.Universe,
    *,
    mode: str = "selection",
    select: str = "all",
    compound: str = "residues",
    dt_fs: float = 500.0,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
    t_min_ps: float = 10.0,
    t_max_ps: float | None = None,
    fft: bool = True,
    unwrap: bool = True,
    msd_type: str = "xyz",
    ndim: int | None = None,
) -> dict:
    """``mode='selection'`` → atom MSD; ``mode='com'`` → molecular COM MSD.

    ``n_frames``: analyse only the first N frames (from ``start``) for testing.
    """
    mode = mode.lower().strip()
    if mode == "selection":
        return msd_from_selection(
            u,
            select=select,
            dt_fs=dt_fs,
            start=start,
            stop=stop,
            step=step,
            n_frames=n_frames,
            fft=fft,
            msd_type=msd_type,
            t_min_ps=t_min_ps,
            t_max_ps=t_max_ps,
            ndim=ndim,
        )
    if mode == "com":
        return msd_from_com(
            u,
            select=select,
            compound=compound,
            dt_fs=dt_fs,
            start=start,
            stop=stop,
            step=step,
            n_frames=n_frames,
            unwrap=unwrap,
            t_min_ps=t_min_ps,
            t_max_ps=t_max_ps,
            ndim=3 if ndim is None else ndim,
        )
    raise ValueError(f"Unknown mode={mode!r}; use 'selection' or 'com'")

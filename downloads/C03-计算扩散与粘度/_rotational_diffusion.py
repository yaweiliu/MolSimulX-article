"""Rotational diffusion from molecular orientation axes or full body frames.

**Single-axis (dipole / bond):**
  C1/C2, geodesic ``⟨θ²⟩≈4 Dr t``, unwrap ``⟨|Φ|²⟩`` (illustrative).

**Body frame (full attitude, SO(3)):**
  Build orthonormal triad R(t); then
  - axis-average C1: ``⟨e_i(0)·e_i(t)⟩`` → ``~A exp(-2 Dr t)``
  - geodesic: rotation angle φ of R_rel → ``⟨φ²⟩≈6 Dr t`` (early)
  - unwrap: accumulate rotvecs → ``⟨|Φ|²⟩≈6 Dr t`` (early)

Use ``n_frames=N`` (or ``stop``) to analyse only the first N frames for testing.
"""

from __future__ import annotations

__version__ = "1.1.1"
__date__ = "2026-07-26"

import numpy as np
import MDAnalysis as mda


def _residue_atom_indices(
    u: mda.Universe,
    select: str,
    *,
    n_per_residue: int | None = None,
    residue_select: str | None = None,
    take: str = "all",
) -> np.ndarray:
    """Atom indices per residue, shape (M, K)."""
    ag = u.select_atoms(select)
    if ag.n_atoms == 0:
        raise ValueError(f"No atoms matched select={select!r}")

    residues = (
        u.select_atoms(residue_select).residues
        if residue_select is not None
        else ag.residues
    )
    ag_set = set(int(i) for i in ag.indices)
    rows: list[list[int]] = []
    for res in residues:
        hit = [int(i) for i in res.atoms.indices if int(i) in ag_set]
        if take == "first" and hit:
            hit = hit[:1]
        elif take != "all":
            raise ValueError(f"take must be 'all' or 'first'; got {take!r}")
        if n_per_residue is not None and len(hit) != n_per_residue:
            raise ValueError(
                f"residue {res.resid}: expected {n_per_residue} atom(s) "
                f"for {select!r}, got {len(hit)}"
            )
        if hit:
            rows.append(hit)
    if not rows:
        raise ValueError(f"No residues for select={select!r}")
    lengths = {len(r) for r in rows}
    if len(lengths) != 1:
        raise ValueError(f"Variable atoms/residue for {select!r}: {sorted(lengths)}")
    return np.asarray(rows, dtype=int)


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


def unit_axes_from_bond(
    u: mda.Universe,
    i_select: str,
    j_select: str,
    *,
    residue_select: str | None = None,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
) -> np.ndarray:
    """Unit vector i→j per residue (first match each). Shape (F, M, 3)."""
    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)
    i_idx = _residue_atom_indices(
        u, i_select, n_per_residue=1, residue_select=residue_select, take="first"
    )[:, 0]
    j_idx = _residue_atom_indices(
        u, j_select, n_per_residue=1, residue_select=residue_select, take="first"
    )[:, 0]
    if len(i_idx) != len(j_idx):
        raise ValueError("i/j residue counts differ")
    frames = []
    for _ts in u.trajectory[start:stop:step]:
        pos = u.atoms.positions
        vec = pos[j_idx] - pos[i_idx]
        nrm = np.linalg.norm(vec, axis=-1, keepdims=True)
        frames.append(vec / np.clip(nrm, 1e-12, None))
    if not frames:
        raise ValueError("No frames selected")
    return np.stack(frames, axis=0)


def unit_axes_from_sites(
    u: mda.Universe,
    origin_select: str,
    target_select: str,
    *,
    n_origin: int = 1,
    n_target: int | None = None,
    residue_select: str | None = None,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
) -> np.ndarray:
    """Unit vector origin → mean(target) per residue. Shape (F, M, 3).

    Water dipole: ``origin_select='type 2'``, ``target_select='type 1'``,
    ``n_target=2``.
    """
    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)
    o_idx = _residue_atom_indices(
        u, origin_select, n_per_residue=n_origin, residue_select=residue_select
    )
    t_idx = _residue_atom_indices(
        u, target_select, n_per_residue=n_target, residue_select=residue_select
    )
    if o_idx.shape[0] != t_idx.shape[0]:
        raise ValueError("origin/target residue counts differ")
    frames = []
    for _ts in u.trajectory[start:stop:step]:
        pos = u.atoms.positions
        origin = pos[o_idx[:, 0]] if o_idx.shape[1] == 1 else pos[o_idx].mean(axis=1)
        target = pos[t_idx].mean(axis=1)
        vec = target - origin
        nrm = np.linalg.norm(vec, axis=-1, keepdims=True)
        frames.append(vec / np.clip(nrm, 1e-12, None))
    if not frames:
        raise ValueError("No frames selected")
    return np.stack(frames, axis=0)


def body_frames_from_sites(
    u: mda.Universe,
    origin_select: str,
    target_select: str,
    *,
    n_origin: int = 1,
    n_target: int = 2,
    residue_select: str | None = None,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
) -> np.ndarray:
    """Orthonormal body frames R(t). Shape (F, M, 3, 3), columns = body axes.

    Water (SHAKE rigid):
      e1 ∥ O → mid(H)          (dipole)
      e3 ∥ (H1−O)×(H2−O)      (plane normal; H ordered by atom index)
      e2 = e3 × e1
    """
    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)
    if int(n_target) < 2:
        raise ValueError("body frame needs n_target>=2 (two sites to span a plane)")
    o_idx = _residue_atom_indices(
        u, origin_select, n_per_residue=n_origin, residue_select=residue_select
    )
    t_idx = _residue_atom_indices(
        u, target_select, n_per_residue=n_target, residue_select=residue_select
    )
    if o_idx.shape[0] != t_idx.shape[0]:
        raise ValueError("origin/target residue counts differ")
    # Stable H ordering within each residue
    t_idx = np.sort(t_idx, axis=1)

    frames = []
    for _ts in u.trajectory[start:stop:step]:
        pos = u.atoms.positions
        origin = pos[o_idx[:, 0]] if o_idx.shape[1] == 1 else pos[o_idx].mean(axis=1)
        h1 = pos[t_idx[:, 0]]
        h2 = pos[t_idx[:, 1]]
        e1 = (h1 + h2) * 0.5 - origin
        e1 = e1 / np.clip(np.linalg.norm(e1, axis=-1, keepdims=True), 1e-12, None)
        e3 = np.cross(h1 - origin, h2 - origin)
        e3 = e3 / np.clip(np.linalg.norm(e3, axis=-1, keepdims=True), 1e-12, None)
        e2 = np.cross(e3, e1)
        e2 = e2 / np.clip(np.linalg.norm(e2, axis=-1, keepdims=True), 1e-12, None)
        # Re-orthogonalize e3 against e1,e2 (numerical)
        e3 = np.cross(e1, e2)
        e3 = e3 / np.clip(np.linalg.norm(e3, axis=-1, keepdims=True), 1e-12, None)
        frames.append(np.stack([e1, e2, e3], axis=-1))  # (M, 3, 3)
    if not frames:
        raise ValueError("No frames selected")
    return np.stack(frames, axis=0)


def orientation_correlation(
    u_vec: np.ndarray, *, max_lag: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """C1 = ⟨u·u⟩, C2 = ⟨(3(u·u)²−1)/2⟩."""
    n_frames = u_vec.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    c1 = np.zeros(max_lag + 1)
    c2 = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        dots = np.sum(u_vec[lag:] * u_vec[: n_frames - lag], axis=-1)
        c1[lag] = np.mean(dots)
        c2[lag] = np.mean(0.5 * (3.0 * dots * dots - 1.0))
    return c1, c2


def body_axis_orientation_correlation(
    Rmats: np.ndarray, *, max_lag: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Average C1/C2 over the three body axes. ``Rmats`` shape (F, M, 3, 3)."""
    n_frames = Rmats.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    c1 = np.zeros(max_lag + 1)
    c2 = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        dots = np.zeros(Rmats.shape[1], dtype=float)
        for k in range(3):
            dots = dots + np.sum(
                Rmats[lag:, :, :, k] * Rmats[: n_frames - lag, :, :, k], axis=-1
            )
        dots = dots / 3.0
        c1[lag] = np.mean(dots)
        c2[lag] = np.mean(0.5 * (3.0 * dots * dots - 1.0))
    return c1, c2


def unwrap_angular_displacement(u_vec: np.ndarray) -> np.ndarray:
    """Cumulative rotation vector Φ(t) for a single unit axis. Shape (F, M, 3)."""
    n_frames, n_mol, _ = u_vec.shape
    phi = np.zeros((n_frames, n_mol, 3), dtype=float)
    for t in range(n_frames - 1):
        a, b = u_vec[t], u_vec[t + 1]
        dots = np.clip(np.sum(a * b, axis=-1), -1.0, 1.0)
        cross = np.cross(a, b)
        sine = np.linalg.norm(cross, axis=-1)
        theta = np.arctan2(sine, dots)
        scale = np.zeros_like(theta)
        ok = sine > 1e-14
        scale[ok] = theta[ok] / sine[ok]
        phi[t + 1] = phi[t] + cross * scale[:, None]
    return phi


def _rotation_angle_from_matrices(r_rel: np.ndarray) -> np.ndarray:
    """Rotation angle φ∈[0,π] from relative matrices ``(..., 3, 3)`` via trace."""
    tr = r_rel[..., 0, 0] + r_rel[..., 1, 1] + r_rel[..., 2, 2]
    cos_phi = np.clip(0.5 * (tr - 1.0), -1.0, 1.0)
    return np.arccos(cos_phi)


def _rotvecs_from_matrices(r_rel: np.ndarray) -> np.ndarray:
    """Rotation vectors from relative matrices ``(..., 3, 3)`` (no SciPy SVD)."""
    # skew-symmetric extraction: ||[R32-R23,...]|| = 2 |sin φ|
    ax = np.stack(
        [
            r_rel[..., 2, 1] - r_rel[..., 1, 2],
            r_rel[..., 0, 2] - r_rel[..., 2, 0],
            r_rel[..., 1, 0] - r_rel[..., 0, 1],
        ],
        axis=-1,
    )
    phi = _rotation_angle_from_matrices(r_rel)
    sine = np.linalg.norm(ax, axis=-1)
    rotvec = np.zeros_like(ax, dtype=float)

    small = phi < 1e-8
    rotvec[small] = 0.5 * ax[small]

    # Dense MD dumps: steps ≪ π; near-π branch almost never hit
    ok = ~small
    scale = np.zeros_like(phi)
    scale[ok] = phi[ok] / np.clip(sine[ok], 1e-14, None)
    rotvec[ok] = ax[ok] * scale[ok, None]
    return rotvec


def unwrap_body_rotvec(Rmats: np.ndarray) -> np.ndarray:
    """Cumulative SO(3) rotation vector from consecutive body frames.

    ``Rmats`` shape (F, M, 3, 3). Step rotation uses ``R(t+1) R(t)^T``.
    """
    n_frames, n_mol = Rmats.shape[:2]
    phi = np.zeros((n_frames, n_mol, 3), dtype=float)
    for t in range(n_frames - 1):
        r_rel = np.einsum("mij,mkj->mik", Rmats[t + 1], Rmats[t])
        phi[t + 1] = phi[t] + _rotvecs_from_matrices(r_rel)
    return phi


def angular_msd_geodesic(
    u_vec: np.ndarray, *, max_lag: int | None = None
) -> np.ndarray:
    """⟨θ(t)²⟩ with θ = arccos(u(0)·u(t)). Primary single-axis angular MSD."""
    n_frames = u_vec.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    amsd = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        dots = np.clip(np.sum(u_vec[lag:] * u_vec[: n_frames - lag], axis=-1), -1.0, 1.0)
        theta = np.arccos(dots)
        amsd[lag] = np.mean(theta * theta)
    return amsd


def angular_msd_unwrapped(
    u_vec: np.ndarray, *, max_lag: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Path-unwrapped ⟨|Φ(t)−Φ(0)|²⟩ and Φ (single axis)."""
    phi = unwrap_angular_displacement(u_vec)
    n_frames = phi.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    amsd = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        d = phi[lag:] - phi[: n_frames - lag]
        amsd[lag] = np.mean(np.sum(d * d, axis=-1))
    return amsd, phi


def body_angular_msd_geodesic(
    Rmats: np.ndarray, *, max_lag: int | None = None
) -> np.ndarray:
    """⟨φ(t)²⟩ with φ = rotation angle of R(t) R(0)^T ∈ [0, π]. Prefactor 6.

    Uses ``φ = arccos((Tr R_rel − 1)/2)`` (no per-lag SciPy SVD).
    """
    n_frames = Rmats.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    amsd = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        # Tr(R_a R_b^T) = sum_ij R_a_ij R_b_ij
        tr = np.einsum(
            "fmij,fmij->fm",
            Rmats[lag:],
            Rmats[: n_frames - lag],
        )
        cos_phi = np.clip(0.5 * (tr - 1.0), -1.0, 1.0)
        ang = np.arccos(cos_phi)
        amsd[lag] = np.mean(ang * ang)
    return amsd


def body_angular_msd_unwrapped(
    Rmats: np.ndarray, *, max_lag: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Path-unwrapped body ⟨|Φ(t)−Φ(0)|²⟩ and Φ. Prefactor 6."""
    phi = unwrap_body_rotvec(Rmats)
    n_frames = phi.shape[0]
    if max_lag is None:
        max_lag = n_frames // 2
    max_lag = min(max_lag, n_frames - 1)
    amsd = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        d = phi[lag:] - phi[: n_frames - lag]
        amsd[lag] = np.mean(np.sum(d * d, axis=-1))
    return amsd, phi


def fit_orientation_correlation(
    times_ps: np.ndarray,
    c: np.ndarray,
    *,
    t_min_ps: float = 0.5,
    t_max_ps: float = 5.0,
    legendre_l: int = 1,
) -> tuple[float, float, slice]:
    """Fit C_l ~ A exp(-l(l+1) Dr t) → Dr [1/ps], A."""
    pref = float(legendre_l * (legendre_l + 1))
    mask = (times_ps >= t_min_ps) & (times_ps <= t_max_ps) & (c > 0.05)
    if int(mask.sum()) < 3:
        raise ValueError(
            f"Not enough C{legendre_l} points in [{t_min_ps}, {t_max_ps}] ps"
        )
    slope, intercept = np.polyfit(times_ps[mask], np.log(c[mask]), 1)
    idx = np.where(mask)[0]
    return (
        float(-slope / pref),
        float(np.exp(intercept)),
        slice(int(idx[0]), int(idx[-1]) + 1),
    )


def fit_angular_msd(
    times_ps: np.ndarray,
    amsd: np.ndarray,
    *,
    t_min_ps: float = 0.2,
    t_max_ps: float = 2.0,
    prefactor: float = 4.0,
) -> tuple[float, slice]:
    """Fit ⟨θ²⟩ = prefactor * Dr * t → Dr [1/ps]."""
    mask = (times_ps >= t_min_ps) & (times_ps <= t_max_ps)
    if int(mask.sum()) < 3:
        raise ValueError("Not enough angular-MSD points in fit window")
    slope, _ = np.polyfit(times_ps[mask], amsd[mask], 1)
    idx = np.where(mask)[0]
    return float(slope / prefactor), slice(int(idx[0]), int(idx[-1]) + 1)


def _analyse_single_axis(
    u_vec: np.ndarray,
    *,
    dt_fs: float,
    step: int,
    c1_t_min_ps: float,
    c1_t_max_ps: float,
    amsd_t_min_ps: float,
    amsd_t_max_ps: float,
    legendre_l: int,
    amsd_prefactor: float,
) -> dict:
    c1, c2 = orientation_correlation(u_vec)
    amsd = angular_msd_geodesic(u_vec)
    amsd_u, phi = angular_msd_unwrapped(u_vec)
    times_ps = np.arange(len(c1), dtype=float) * (dt_fs * step) / 1000.0

    series = c2 if legendre_l == 2 else c1
    dr_c, amp, fit_c = fit_orientation_correlation(
        times_ps,
        series,
        t_min_ps=c1_t_min_ps,
        t_max_ps=c1_t_max_ps,
        legendre_l=legendre_l,
    )
    dr_a, fit_a = fit_angular_msd(
        times_ps,
        amsd,
        t_min_ps=amsd_t_min_ps,
        t_max_ps=amsd_t_max_ps,
        prefactor=amsd_prefactor,
    )
    dr_u, fit_u = fit_angular_msd(
        times_ps,
        amsd_u,
        t_min_ps=amsd_t_min_ps,
        t_max_ps=amsd_t_max_ps,
        prefactor=amsd_prefactor,
    )
    return {
        "mode": "single_axis",
        "u": u_vec,
        "phi": phi,
        "times_ps": times_ps,
        "n_frames_used": int(u_vec.shape[0]),
        "C1": c1,
        "C2": c2,
        "angular_msd": amsd,
        "angular_msd_unwrapped": amsd_u,
        "Dr_C1_per_ps": dr_c,
        "C1_amp": amp,
        "Dr_amsd_per_ps": dr_a,
        "Dr_amsd_unwrapped_per_ps": dr_u,
        "fit_slice_c1": fit_c,
        "fit_slice_amsd": fit_a,
        "fit_slice_amsd_unwrapped": fit_u,
        "amsd_prefactor": amsd_prefactor,
    }


def _analyse_body_frame(
    Rmats: np.ndarray,
    *,
    dt_fs: float,
    step: int,
    c1_t_min_ps: float,
    c1_t_max_ps: float,
    amsd_t_min_ps: float,
    amsd_t_max_ps: float,
    legendre_l: int,
    amsd_prefactor: float = 6.0,
) -> dict:
    c1, c2 = body_axis_orientation_correlation(Rmats)
    amsd = body_angular_msd_geodesic(Rmats)
    amsd_u, phi = body_angular_msd_unwrapped(Rmats)
    times_ps = np.arange(len(c1), dtype=float) * (dt_fs * step) / 1000.0

    series = c2 if legendre_l == 2 else c1
    dr_c, amp, fit_c = fit_orientation_correlation(
        times_ps,
        series,
        t_min_ps=c1_t_min_ps,
        t_max_ps=c1_t_max_ps,
        legendre_l=legendre_l,
    )
    dr_a, fit_a = fit_angular_msd(
        times_ps,
        amsd,
        t_min_ps=amsd_t_min_ps,
        t_max_ps=amsd_t_max_ps,
        prefactor=amsd_prefactor,
    )
    dr_u, fit_u = fit_angular_msd(
        times_ps,
        amsd_u,
        t_min_ps=amsd_t_min_ps,
        t_max_ps=amsd_t_max_ps,
        prefactor=amsd_prefactor,
    )
    return {
        "mode": "body_frame",
        "R": Rmats,
        "phi": phi,
        "times_ps": times_ps,
        "n_frames_used": int(Rmats.shape[0]),
        "C1": c1,
        "C2": c2,
        "angular_msd": amsd,
        "angular_msd_unwrapped": amsd_u,
        "Dr_C1_per_ps": dr_c,
        "C1_amp": amp,
        "Dr_amsd_per_ps": dr_a,
        "Dr_amsd_unwrapped_per_ps": dr_u,
        "fit_slice_c1": fit_c,
        "fit_slice_amsd": fit_a,
        "fit_slice_amsd_unwrapped": fit_u,
        "amsd_prefactor": amsd_prefactor,
    }


def rotational_diffusion(
    u: mda.Universe | None = None,
    *,
    axes: np.ndarray | None = None,
    body_frames: np.ndarray | None = None,
    orientation: str = "sites",
    origin_select: str | None = None,
    target_select: str | None = None,
    n_target: int | None = None,
    bond: tuple[str, str] | None = None,
    residue_select: str | None = None,
    dt_fs: float = 20.0,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
    c1_t_min_ps: float = 0.5,
    c1_t_max_ps: float = 5.0,
    amsd_t_min_ps: float = 0.2,
    amsd_t_max_ps: float = 2.0,
    legendre_l: int = 1,
    amsd_prefactor: float | None = None,
) -> dict:
    """Rotational diffusion from single-axis or full body-frame attitude.

    Provide one of:

    - ``axes`` ``(F, M, 3)`` — single unit axes
    - ``body_frames`` ``(F, M, 3, 3)`` — precomputed R(t)
    - ``orientation='sites'|'bond'`` — single-axis builders
    - ``orientation='body'|'body_frame'`` — full attitude from O + 2 H

    ``n_frames``: analyse only the first N frames (from ``start``) for testing.

    Single-axis MSD prefactor default **4**; body-frame default **6**.
    """
    orientation = (orientation or "sites").lower().strip()
    start, stop, step = _resolve_frame_slice(start, stop, step, n_frames)

    if body_frames is not None or orientation in ("body", "body_frame"):
        if body_frames is not None:
            Rmats = np.asarray(body_frames, dtype=float)
        else:
            if u is None:
                raise ValueError("Pass Universe u or body_frames=")
            if not origin_select or not target_select:
                raise ValueError("body frame needs origin_select and target_select")
            Rmats = body_frames_from_sites(
                u,
                origin_select,
                target_select,
                n_origin=1,
                n_target=2 if n_target is None else int(n_target),
                residue_select=residue_select,
                start=start,
                stop=stop,
                step=step,
            )
        if Rmats.ndim != 4 or Rmats.shape[-2:] != (3, 3):
            raise ValueError("body_frames must have shape (F, M, 3, 3)")
        pref = 6.0 if amsd_prefactor is None else float(amsd_prefactor)
        return _analyse_body_frame(
            Rmats,
            dt_fs=dt_fs,
            step=step,
            c1_t_min_ps=c1_t_min_ps,
            c1_t_max_ps=c1_t_max_ps,
            amsd_t_min_ps=amsd_t_min_ps,
            amsd_t_max_ps=amsd_t_max_ps,
            legendre_l=legendre_l,
            amsd_prefactor=pref,
        )

    if axes is not None:
        u_vec = np.asarray(axes, dtype=float)
        if u_vec.ndim != 3 or u_vec.shape[-1] != 3:
            raise ValueError("axes must have shape (F, M, 3)")
    else:
        if u is None:
            raise ValueError("Pass Universe u or axes=")
        if bond is not None:
            orientation = "bond"
        if orientation == "sites":
            if not origin_select or not target_select:
                raise ValueError("sites needs origin_select and target_select")
            u_vec = unit_axes_from_sites(
                u,
                origin_select,
                target_select,
                n_origin=1,
                n_target=n_target,
                residue_select=residue_select,
                start=start,
                stop=stop,
                step=step,
            )
        elif orientation == "bond":
            if bond is None:
                raise ValueError("bond needs bond=(i_select, j_select)")
            u_vec = unit_axes_from_bond(
                u,
                bond[0],
                bond[1],
                residue_select=residue_select,
                start=start,
                stop=stop,
                step=step,
            )
        else:
            raise ValueError(
                "orientation must be 'sites', 'bond', or 'body'/'body_frame' "
                "(or pass axes=/body_frames=)"
            )

    pref = 4.0 if amsd_prefactor is None else float(amsd_prefactor)
    return _analyse_single_axis(
        u_vec,
        dt_fs=dt_fs,
        step=step,
        c1_t_min_ps=c1_t_min_ps,
        c1_t_max_ps=c1_t_max_ps,
        amsd_t_min_ps=amsd_t_min_ps,
        amsd_t_max_ps=amsd_t_max_ps,
        legendre_l=legendre_l,
        amsd_prefactor=pref,
    )

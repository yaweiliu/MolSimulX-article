"""Nematic order parameter $S_2$ for rigid overlapping-sphere rods.

Trajectory should be **unwrapped** (LAMMPS ``xsu ysu zsu``) so end-to-end
vectors are not broken by the box.

Rod axis per molecule (residue):

    u = (r_end - r_start) / |r_end - r_start|

Order tensor (average over rods):

    Q = < 3/2 u u^T - 1/2 I >

$S_2$ = largest eigenvalue of $Q$; director $\\hat n$ = corresponding eigenvector.

Use ``n_frames=N`` to analyse only the first N frames for testing.
"""

from __future__ import annotations

__version__ = "1.0.0"
__date__ = "2026-08-01"

import numpy as np


def _resolve_frame_slice(
    start: int | None,
    stop: int | None,
    step: int,
    n_frames: int | None,
) -> tuple[int, int | None, int]:
    start_i = 0 if start is None else int(start)
    if n_frames is not None:
        n = int(n_frames)
        if n <= 0:
            raise ValueError(f"n_frames must be positive; got {n_frames!r}")
        stop_i = start_i + n
        if stop is not None:
            stop_i = min(stop_i, int(stop))
        return start_i, stop_i, int(step)
    stop_i = None if stop is None else int(stop)
    return start_i, stop_i, int(step)


def rod_unit_vectors(
    positions: np.ndarray,
    *,
    n_beads: int = 11,
) -> np.ndarray:
    """Unit directors from first/last bead of each rod.

    ``positions`` shape ``(n_atoms, 3)``; atoms must be contiguous blocks of
    ``n_beads`` (LAMMPS ``dump_modify sort id`` + sequential mol atom ids).
    """
    pos = np.asarray(positions, dtype=float)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"positions must be (n_atoms, 3); got {pos.shape}")
    n_atoms = pos.shape[0]
    if n_atoms % int(n_beads) != 0:
        raise ValueError(
            f"n_atoms={n_atoms} not divisible by n_beads={n_beads}"
        )
    rods = pos.reshape(n_atoms // int(n_beads), int(n_beads), 3)
    d = rods[:, -1, :] - rods[:, 0, :]
    norms = np.linalg.norm(d, axis=1, keepdims=True)
    if np.any(norms < 1e-12):
        raise ValueError("zero-length rod end-to-end vector")
    return d / norms


def nematic_q_tensor(directors: np.ndarray) -> np.ndarray:
    """Build $Q = \\langle 3/2\\,uu^T - 1/2\\,I\\rangle$ from unit directors."""
    u = np.asarray(directors, dtype=float)
    if u.ndim != 2 or u.shape[1] != 3:
        raise ValueError(f"directors must be (n_rods, 3); got {u.shape}")
    if u.shape[0] < 1:
        raise ValueError("need at least one director")
    # Q_ab = 3/2 <u_a u_b> - 1/2 δ_ab
    uu = (u[:, :, None] * u[:, None, :]).mean(axis=0)
    return 1.5 * uu - 0.5 * np.eye(3)


def s2_from_directors(directors: np.ndarray) -> tuple[float, np.ndarray]:
    """Return $(S_2, \\hat n)$ from rod directors."""
    Q = nematic_q_tensor(directors)
    evals, evecs = np.linalg.eigh(Q)
    idx = int(np.argmax(evals))
    n_hat = evecs[:, idx]
    # fix arbitrary sign for continuity across callers
    if n_hat[np.argmax(np.abs(n_hat))] < 0:
        n_hat = -n_hat
    return float(evals[idx]), n_hat


def number_density(n_particles: int, dimensions) -> float:
    """Number density $N/V$ from MDAnalysis ``ts.dimensions`` (orthorhombic)."""
    dims = np.asarray(dimensions, dtype=float)
    vol = float(dims[0] * dims[1] * dims[2])
    if vol <= 0:
        raise ValueError(f"non-positive volume from dimensions={dimensions}")
    return float(n_particles) / vol


def close_packing_density(L: float = 5.0, D: float = 1.0) -> float:
    """Close-packing rod number density $\\rho_{cp}$.

    $$
    \\rho_{cp} = \\frac{2}{\\sqrt{2} + (L/D)\\sqrt{3}}
    $$
    """
    aspect = float(L) / float(D)
    return 2.0 / (np.sqrt(2.0) + aspect * np.sqrt(3.0))


def relative_density(
    density,
    *,
    kind: str = "atom",
    n_beads: int = 11,
    L: float = 5.0,
    D: float = 1.0,
) -> np.ndarray | float:
    """Reduced density relative to close packing: $\\rho^*=\\rho/\\rho_{cp}$.

    - ``kind='atom'``: ``density`` = $N_\\mathrm{atom}/V$ (LAMMPS lj density if $m=1$)
      → $\\rho = \\rho_\\mathrm{atom}/n_\\mathrm{beads}$
    - ``kind='rod'``: ``density`` = $N_\\mathrm{rod}/V$ → $\\rho$ directly
    """
    dens = np.asarray(density, dtype=float)
    if kind == "atom":
        rho = dens / float(n_beads)
    elif kind == "rod":
        rho = dens
    else:
        raise ValueError("kind must be 'atom' or 'rod'")
    rho_star = rho / close_packing_density(L, D)
    if np.ndim(rho_star) == 0:
        return float(rho_star)
    return rho_star


# backward-compatible aliases (old packing-fraction API)
def packing_fraction(*args, **kwargs):
    """Deprecated alias of :func:`relative_density`."""
    return relative_density(*args, **kwargs)


def compute_s2_trajectory(
    universe,
    *,
    n_beads: int = 11,
    dt: float = 1.0,
    start: int | None = None,
    stop: int | None = None,
    step: int = 1,
    n_frames: int | None = None,
    density_particles: str = "rods",
    rod_L: float = 5.0,
    rod_D: float = 1.0,
) -> dict:
    """Compute $S_2(t)$ (and density) along a trajectory.

    Parameters
    ----------
    universe :
        MDAnalysis Universe with unwrapped coordinates.
    n_beads :
        Beads per rod (C04 default 11).
    dt :
        Time between consecutive dump frames (lj $\\tau$ or fs — caller choice).
    n_frames :
        If set, only the first N frames from ``start`` (debug).
    density_particles :
        ``\"rods\"`` → $N_\\mathrm{rod}/V$; ``\"atoms\"`` → $N_\\mathrm{atom}/V$.

    Returns
    -------
    dict with keys:
        ``times``, ``S2``, ``density`` (rod or atom number density),
        ``rho_star`` ($\\rho^*=\\rho/\\rho_{cp}$), ``n_hat``, ``n_rods``, …
    """
    start_i, stop_i, step_i = _resolve_frame_slice(start, stop, step, n_frames)
    traj = universe.trajectory
    n_atoms = universe.atoms.n_atoms
    n_rods = n_atoms // int(n_beads)

    times = []
    s2_list = []
    dens_list = []
    n_hat_list = []

    # align director sign to first frame for smoother plots
    n_ref = None

    for ts in traj[start_i:stop_i:step_i]:
        directors = rod_unit_vectors(universe.atoms.positions, n_beads=n_beads)
        s2, n_hat = s2_from_directors(directors)
        if n_ref is None:
            n_ref = n_hat.copy()
        elif float(np.dot(n_hat, n_ref)) < 0:
            n_hat = -n_hat

        if density_particles == "rods":
            dens = number_density(n_rods, ts.dimensions)
        elif density_particles == "atoms":
            dens = number_density(n_atoms, ts.dimensions)
        else:
            raise ValueError(
                f"density_particles must be 'rods' or 'atoms'; got {density_particles!r}"
            )

        times.append(float(ts.frame) * float(dt))
        s2_list.append(s2)
        dens_list.append(dens)
        n_hat_list.append(n_hat)

    dens_arr = np.asarray(dens_list, dtype=float)
    rho_star = relative_density(
        dens_arr,
        kind="rod" if density_particles == "rods" else "atom",
        n_beads=n_beads,
        L=rod_L,
        D=rod_D,
    )
    rho_star = np.asarray(rho_star, dtype=float)

    return {
        "times": np.asarray(times, dtype=float),
        "S2": np.asarray(s2_list, dtype=float),
        "density": dens_arr,
        "rho_star": rho_star,
        "eta": rho_star,  # alias
        "n_hat": np.asarray(n_hat_list, dtype=float),
        "n_rods": int(n_rods),
        "n_frames": len(s2_list),
        "dt": float(dt),
        "n_beads": int(n_beads),
        "rod_L": float(rod_L),
        "rod_D": float(rod_D),
        "rho_cp": close_packing_density(rod_L, rod_D),
    }


def summarize_s2(
    result: dict,
    *,
    early_frac: float = 0.1,
    late_frac: float = 0.1,
) -> dict:
    """Mean $S_2$ / $\\rho^*$ over early and late windows of a compress run."""
    s2 = np.asarray(result["S2"], dtype=float)
    rho_star = np.asarray(
        result.get("rho_star", result.get("eta", result["density"])),
        dtype=float,
    )
    n = len(s2)
    if n < 2:
        raise ValueError("need at least 2 frames to summarize")
    n_early = max(1, int(round(n * early_frac)))
    n_late = max(1, int(round(n * late_frac)))
    return {
        "S2_early": float(s2[:n_early].mean()),
        "S2_late": float(s2[-n_late:].mean()),
        "S2_mean": float(s2.mean()),
        "rho_star_early": float(rho_star[:n_early].mean()),
        "rho_star_late": float(rho_star[-n_late:].mean()),
        "eta_early": float(rho_star[:n_early].mean()),  # alias
        "eta_late": float(rho_star[-n_late:].mean()),
        "n_frames": n,
        "n_rods": int(result.get("n_rods", -1)),
    }

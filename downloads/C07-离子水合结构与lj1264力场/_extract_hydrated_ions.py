"""Extract ion + nearby water molecules to XYZ (hydration-shell clusters).

Generic helper for aqueous ion trajectories (not tied to one salt recipe):

* pick any ion / water-O with MDAnalysis selections;
* for each frame × each ion, keep waters whose **oxygen** is within
  ``cutoff`` Å (minimum-image);
* write the ion + whole water residues, recentered on the ion with MIC
  so the cluster is contiguous in the XYZ.

Typical cutoffs (tune to the first RDF minimum of that ion–Ow pair):

* divalent cations (Mg²⁺, …) ≈ 3.0–3.5 Å
* halide anions (Cl⁻, …) ≈ 3.8–4.5 Å

Output names default to ``{element}{ii:02d}_f{frame:04d}.xyz`` under
``out_dir`` (override with ``ion_label``).
"""

from __future__ import annotations

__version__ = "1.1.0"
__date__ = "2026-08-13"

from pathlib import Path

import numpy as np

from _helper_functions import load_lammps_universe


def _mic_delta(dx: np.ndarray, box: np.ndarray) -> np.ndarray:
    """Minimum-image delta for orthorhombic box lengths ``box[:3]``."""
    L = np.asarray(box[:3], dtype=float)
    out = np.asarray(dx, dtype=float).copy()
    for i in range(3):
        if L[i] <= 0:
            continue
        out[..., i] -= L[i] * np.rint(out[..., i] / L[i])
    return out


def _atom_element(atom) -> str:
    sym = getattr(atom, "element", None) or "X"
    if isinstance(sym, (bytes, bytearray)):
        sym = sym.decode()
    return str(sym)


def _write_xyz(path: Path, symbols: list[str], coords: np.ndarray, comment: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(symbols)
    lines = [str(n), comment]
    for sym, (x, y, z) in zip(symbols, coords):
        lines.append(f"{sym:4s} {x:12.6f} {y:12.6f} {z:12.6f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _default_ion_label(ions) -> str:
    """Use the first ion's element symbol when ``ion_label`` is omitted."""
    if len(ions) == 0:
        return "Ion"
    return _atom_element(ions[0])


def build_resnames(
    *groups: tuple[str, int],
) -> list[str] | None:
    """Build a flat residue-name list, e.g. ``("Mg", 2), ("Cl", 4), ("H2O", 800)``.

    Returns ``None`` if every count is zero (caller may omit resnames).
    """
    names: list[str] = []
    for name, count in groups:
        n = int(count)
        if n < 0:
            raise ValueError(f"residue count must be >= 0; got {name}={count!r}")
        if n:
            names.extend([str(name)] * n)
    return names or None


def extract_hydrated_ions(
    topo,
    traj,
    *,
    out_dir="hydrated_ion",
    ion_sel="type 1",
    water_o_sel="type 4",
    cutoff=3.2,
    start=0,
    stop=None,
    step=10,
    dt_fs=2000.0,
    resnames=None,
    ion_label=None,
    type_to_element=None,
):
    """Write ion + hydration-shell water XYZ files.

    Parameters
    ----------
    topo, traj
        LAMMPS data + dump (prefer unwrapped ``xsu ysu zsu``).
    out_dir
        Output directory (created if missing).
    ion_sel, water_o_sel
        MDAnalysis selections for the central ion(s) and water oxygen.
    cutoff
        Ow–ion distance cutoff in Å (match the ion–Ow RDF first minimum).
    start, stop, step
        Trajectory slice (``stop=None`` → end).
    dt_fs
        Time between dump frames [fs], passed to the loader.
    resnames
        Optional per-residue names (length = n_residues, resid ascending).
        Not required for extraction; only for nicer Universe residue labels.
    ion_label
        Filename prefix, e.g. ``Mg`` → ``Mg01_f0000.xyz``.  Default: element
        of the first selected ion.
    type_to_element
        Optional type→element map; otherwise parsed from data Masses.

    Returns
    -------
    pathlib.Path
        The output directory.
    """
    from MDAnalysis.lib.distances import distance_array

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    u = load_lammps_universe(
        topo,
        traj,
        dt_fs=dt_fs,
        resnames=resnames,
        type_to_element=type_to_element,
    )
    ions = u.select_atoms(ion_sel)
    water_o = u.select_atoms(water_o_sel)
    if len(ions) == 0:
        raise ValueError(f"no ions matched selection {ion_sel!r}")
    if len(water_o) == 0:
        raise ValueError(f"no water O matched selection {water_o_sel!r}")

    label = str(ion_label) if ion_label else _default_ion_label(ions)

    n_frames = u.trajectory.n_frames
    if stop is None or stop < 0:
        stop = n_frames
    stop = min(int(stop), n_frames)
    start = max(0, int(start))
    step = max(1, int(step))
    cutoff = float(cutoff)

    n_written = 0
    for ts in u.trajectory[start:stop:step]:
        box = ts.dimensions
        frame_i = int(ts.frame)
        ion_pos = ions.positions
        ow_pos = water_o.positions
        dmat = distance_array(ion_pos, ow_pos, box=box)

        for i_ion, ion in enumerate(ions):
            hit = np.where(dmat[i_ion] <= cutoff)[0]
            ow_hits = water_o[hit]
            if len(ow_hits) == 0:
                cluster = ion.universe.select_atoms(f"index {ion.index}")
            else:
                resids = sorted({int(a.resid) for a in ow_hits})
                sel = " or ".join(f"resid {r}" for r in resids)
                waters = u.select_atoms(sel)
                cluster = ion + waters

            ref = ion.position.copy()
            coords = cluster.positions.copy()
            coords = ref + _mic_delta(coords - ref, box)
            symbols = [_atom_element(atom) for atom in cluster]

            fname = out / f"{label}{i_ion + 1:02d}_f{frame_i:04d}.xyz"
            comment = (
                f"{label}#{i_ion + 1} frame={frame_i} cutoff={cutoff:.3f}A "
                f"n_water={len(ow_hits)} n_atoms={len(cluster)}"
            )
            _write_xyz(fname, symbols, coords, comment=comment)
            n_written += 1

    print(
        f"wrote {n_written} XYZ → {out.resolve()}  "
        f"(ions={len(ions)}, label={label}, cutoff={cutoff} Å, "
        f"frames={start}:{stop}:{step})"
    )
    return out


def main(argv=None):
    import argparse

    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--topo", default="./result_atoms.eq.data")
    p.add_argument("--traj", default="./result_atoms.lammpstrj")
    p.add_argument("--out-dir", default="hydrated_ion")
    p.add_argument(
        "--ion-sel",
        default="type 1",
        help="MDAnalysis selection for central ion(s) (default: type 1)",
    )
    p.add_argument(
        "--water-o-sel",
        default="type 4",
        help="MDAnalysis selection for water oxygen (default: type 4)",
    )
    p.add_argument(
        "--cutoff",
        type=float,
        default=3.2,
        help="Ow–ion cutoff [Å]; match RDF first minimum (default: 3.2)",
    )
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--stop", type=int, default=None)
    p.add_argument("--step", type=int, default=10)
    p.add_argument("--dt-fs", type=float, default=2000.0)
    p.add_argument(
        "--ion-label",
        default=None,
        help="XYZ filename prefix (default: element of first ion)",
    )
    p.add_argument(
        "--resname",
        action="append",
        default=None,
        metavar="NAME:COUNT",
        help=(
            "optional residue labels, e.g. --resname Mg:2 --resname Cl:4 "
            "--resname H2O:800 (repeatable; omit to skip resnames)"
        ),
    )
    args = p.parse_args(argv)

    resnames = None
    if args.resname:
        groups: list[tuple[str, int]] = []
        for item in args.resname:
            if ":" not in item:
                raise SystemExit(
                    f"--resname expects NAME:COUNT, got {item!r}"
                )
            name, _, count_s = item.partition(":")
            groups.append((name.strip(), int(count_s)))
        resnames = build_resnames(*groups)

    extract_hydrated_ions(
        args.topo,
        args.traj,
        out_dir=args.out_dir,
        ion_sel=args.ion_sel,
        water_o_sel=args.water_o_sel,
        cutoff=args.cutoff,
        start=args.start,
        stop=args.stop,
        step=args.step,
        dt_fs=args.dt_fs,
        resnames=resnames,
        ion_label=args.ion_label,
    )


if __name__ == "__main__":
    main()

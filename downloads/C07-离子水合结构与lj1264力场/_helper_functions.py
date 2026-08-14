"""Helpers for LAMMPS + MDAnalysis notebooks.

- ``Trajectory`` / ``load_lammps_universe``: data + dump → Universe
- ``get_type_element_map``: type → element from Masses comments
- ``read_result_thermo``: parse ``log.lammps`` thermo blocks
- ``write_xyz`` / ``move_origin_*``: export & display transforms
- ``save_nglview_frame``: export one nglview frame to PNG
"""

from __future__ import annotations

__version__ = "1.1.0"
__date__ = "2026-07-26"

import base64
import re
import time
from pathlib import Path

import numpy as np
import MDAnalysis as mda


class Trajectory(mda.Universe):
    @classmethod
    def read_lammps_dump(cls, topo, traj, type_to_element=None, resnames=None, dt=1.0):
        """Load LAMMPS data + dump; optionally attach elements and resnames."""
        u = mda.Universe(topo, atom_style="id resid type charge x y z")

        if type_to_element:
            elements = []
            for atom in u.atoms:
                try:
                    type_id = int(atom.type)
                except Exception:
                    type_id = None
                if type_id is not None and type_id in type_to_element:
                    elements.append(type_to_element[type_id])
                else:
                    elements.append("C")
                    print(
                        f"Warning: no element for type '{atom.type}' "
                        f"(id {type_id}); using 'C'."
                    )
            u.add_TopologyAttr("element", values=elements)

        if resnames is not None:
            # 与 C02/C03 相同：resnames 长度 = n_residues，按 resid 升序对应 LAMMPS mol
            try:
                u.add_TopologyAttr("resnames", values=resnames)
            except ValueError:
                u.residues.resnames = list(resnames)

        u.load_new(traj, format="LAMMPSDUMP", timeunit="fs", dt=dt)
        print(f"box dimensions: {u.dimensions}")
        print(f"frame num: {u.trajectory.n_frames}")
        u.__class__ = cls
        return u

    def write_xyz(self, connect=False, charge=False, start=0, stop=-1, step=1, dir="."):
        """Write frames to xyz (+ optional box / charge / CONECT files)."""
        output_dir = Path(dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        boxes = []
        charges = [] if charge else None
        if stop == -1:
            stop = self.trajectory.n_frames

        with mda.Writer(str(output_dir / "result_atoms.xyz"), self.atoms.n_atoms) as XYZ:
            self.trajectory[0]
            for _ts in self.trajectory[start:stop:step]:
                XYZ.write(self.atoms)
                boxes.append(np.copy(self.dimensions[0:3]))
                if charge:
                    charges.extend(list(self.atoms.charges))

        np.savetxt(
            str(output_dir / "result_box.dat"),
            np.asarray(boxes),
            fmt="%12.6f %12.6f %12.6f",
            comments="",
        )
        if charge:
            np.savetxt(
                str(output_dir / "result_charge.dat"),
                np.asarray(charges)[:, None],
                comments="",
            )
        if connect:
            # 1-based serial = XYZ / VMD 原子顺序（不用 LAMMPS atom id，避免与文件行序错位）
            with open(str(output_dir / "result_connect.dat"), "w") as fh:
                for atom in self.atoms:
                    serials = [str(atom.ix + 1)]
                    for other in atom.bonded_atoms:
                        serials.append(str(other.ix + 1))
                    fh.write("CONECT " + " ".join(serials) + "\n")


def move_origin_to_corner(ts):
    ts.positions += ts.dimensions[:3] / 2
    return ts


def move_origin_to_center(ts):
    ts.positions -= ts.dimensions[:3] / 2
    return ts


def save_nglview_frame(
    view,
    filename="last_frame.png",
    *,
    frame=-1,
    factor=4,
    antialias=True,
    trim=True,
    transparent=True,
    settle_s=1.0,
    render_wait_s=2.0,
    poll_s=0.1,
):
    """Save one nglview frame as PNG.

    ``frame=-1`` (default) selects the last frame (``view.max_frame``).
    ``render_image`` is asynchronous; this polls ``view._image_data``
    until it updates (do **not** assign ``None`` — the trait expects str).
    """
    out = Path(filename)
    out.parent.mkdir(parents=True, exist_ok=True)

    max_frame = int(getattr(view, "max_frame", 0) or 0)
    if frame is None or int(frame) < 0:
        frame_i = max_frame
    else:
        frame_i = int(frame)
        if frame_i > max_frame:
            raise ValueError(f"frame={frame_i} > max_frame={max_frame}")

    view.frame = frame_i
    time.sleep(float(settle_s))

    prev = getattr(view, "_image_data", "") or ""
    view.render_image(
        factor=factor,
        antialias=antialias,
        trim=trim,
        transparent=transparent,
    )

    deadline = time.time() + float(render_wait_s)
    data = prev
    while time.time() < deadline:
        time.sleep(float(poll_s))
        data = getattr(view, "_image_data", "") or ""
        if data and data != prev:
            break

    if not data:
        raise RuntimeError(
            "nglview did not return image data; increase render_wait_s "
            "or ensure the widget is displayed in the notebook."
        )
    out.write_bytes(base64.b64decode(data))
    print(f"saved: {out}  (frame = {frame_i} / {max_frame})")
    return out


def get_type_element_map(lmp_datafile):
    """Parse ``{type_id: element}`` from Masses comments in a LAMMPS data file."""
    el_names = [
        "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al",
        "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe",
        "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr",
        "Y", "Zr", "Nb", "Mo", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb",
        "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd",
        "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os",
        "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Th", "Pa", "U",
    ]
    path = Path(lmp_datafile)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    start = None
    for idx, ln in enumerate(lines):
        if ln.strip().lower().startswith("masses"):
            start = idx + 1
            break
    if start is None:
        raise ValueError(f"No 'Masses' section in {path}")

    i = start
    while i < len(lines) and lines[i].strip() == "":
        i += 1

    found_hash = False
    type_to_element = {}
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if line == "" or not line[0].isdigit():
            break
        if line.lstrip().startswith("#"):
            i += 1
            continue
        parts = raw.split("#", 1)
        data = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""
        if "#" in raw:
            found_hash = True
        toks = data.split()
        if len(toks) < 2:
            i += 1
            continue
        try:
            type_id = int(toks[0])
        except ValueError:
            i += 1
            continue
        symbol = None
        if comment:
            m = re.search(r"[A-Za-z]+", comment)
            if m:
                seq = m.group(0)
                if len(seq) >= 2:
                    cand2 = seq[:2].capitalize()
                    if cand2 in el_names:
                        symbol = cand2
                if symbol is None:
                    cand1 = seq[0].upper()
                    if cand1 in el_names:
                        symbol = cand1
        if symbol is None:
            symbol = "C"
            print(
                f"Warning: could not parse element for type {type_id} "
                f"from '{comment}'; using 'C'."
            )
        type_to_element[type_id] = symbol
        i += 1

    if not found_hash:
        raise ValueError(f"No '#' comment in Masses of {path}")
    if not type_to_element:
        raise ValueError(f"No mass entries in {path}")
    return type_to_element


def load_lammps_universe(
    topo,
    traj,
    *,
    dt_fs=1.0,
    type_to_element=None,
    resnames=None,
    n_residues=None,
    resname="MOL",
):
    """Load LAMMPS data + dump (prefer unwrapped ``xsu ysu zsu``).

    If ``type_to_element`` is omitted, try sibling ``data.lmp`` then ``topo``.
    If ``resnames`` is omitted and ``n_residues`` is set, use
    ``[resname] * n_residues``.
    """
    topo = Path(topo)
    traj = Path(traj)

    if type_to_element is None:
        candidates = []
        sibling = topo.with_name("data.lmp")
        if sibling.exists() and sibling.resolve() != topo.resolve():
            candidates.append(sibling)
        candidates.append(topo)
        for guess in candidates:
            try:
                type_to_element = get_type_element_map(guess)
                break
            except Exception:
                continue

    if resnames is None and n_residues is not None:
        resnames = [resname] * int(n_residues)

    return Trajectory.read_lammps_dump(
        str(topo),
        str(traj),
        type_to_element=type_to_element,
        resnames=resnames,
        dt=dt_fs,
    )


def read_result_thermo(filename="log.lammps", segment=-1):
    """Read thermo block(s) from a LAMMPS log.

    ``segment=-1`` last block; ``0,1,…`` that block; ``None`` all blocks
    with a ``segment`` column. Column names lowercased; ``v_``/``c_`` stripped.
    """
    import io
    import pandas as pd

    path = Path(filename)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    header_idxs = [i for i, line in enumerate(lines) if line.lstrip().startswith("Step")]
    if not header_idxs:
        raise ValueError(f"No thermo header (line starting with 'Step') in {path}")

    def _parse_block(header_i: int) -> pd.DataFrame:
        chunk = [lines[header_i]]
        for line in lines[header_i + 1 :]:
            s = line.strip()
            if not s:
                break
            if s.startswith(("Loop", "Performance", "MPI", "WARNING", "ERROR")):
                break
            if not (s[0].isdigit() or s[0] in "+-"):
                break
            chunk.append(line)
        if len(chunk) < 2:
            return pd.DataFrame()
        frame = pd.read_csv(io.StringIO("".join(chunk)), sep=r"\s+")
        frame.columns = [
            str(c).lower().removeprefix("v_").removeprefix("c_") for c in frame.columns
        ]
        return frame

    frames = [f for f in (_parse_block(i) for i in header_idxs) if not f.empty]
    if not frames:
        raise ValueError(f"Thermo headers found but no data rows in {path}")

    if segment is None:
        parts = []
        for seg_id, frame in enumerate(frames):
            part = frame.copy()
            part.insert(0, "segment", seg_id)
            parts.append(part)
        return pd.concat(parts, ignore_index=True)

    n = len(frames)
    idx = segment if segment >= 0 else segment + n
    if idx < 0 or idx >= n:
        raise IndexError(f"segment={segment} out of range; log has {n} block(s)")
    return frames[idx].reset_index(drop=True)

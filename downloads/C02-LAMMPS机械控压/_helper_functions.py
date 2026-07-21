"""Helpers for reading LAMMPS trajectories with MDAnalysis (notebook use).

- ``Trajectory``: an :class:`MDAnalysis.Universe` subclass that reads a LAMMPS
  *data* file (topology) plus a LAMMPS *dump* file (trajectory), attaches
  per-atom ``element`` and per-residue ``resnames``, and can export the frames
  to xyz together with box / charge / connectivity side files.
- ``get_type_element_map``: parse ``{type_id: element}`` from the ``Masses``
  section comments of a LAMMPS data file (as written by msxbox / fftool).
- ``move_origin_to_center`` / ``move_origin_to_corner``: on-the-fly coordinate
  shifts usable as MDAnalysis trajectory transformations.

Typical notebook usage::

    from _helper_functions import *

    type_to_element = get_type_element_map('data.lmp')
    u = Trajectory.read_lammps_dump(
            'result_atoms.data', 'result_atoms.lammpstrj',
            type_to_element=type_to_element,
            resnames=['up'] + ['low'] + ['h2o'] * 9000,
            dt=10000)

    thermo = read_result_thermo('log.lammps')
"""

import re
import numpy as np
import MDAnalysis as mda
from MDAnalysis import transformations
from pathlib import Path


class Trajectory(mda.Universe):
    @classmethod
    def read_lammps_dump(cls, topo, traj, type_to_element=None, resnames=None, dt=1):
        """
        Create a properly initialized MDAnalysis Universe, attach 'element' and 'resnames'
        if supplied, then convert the instance to Trajectory and return it.
        """
        # create a proper Universe so MDAnalysis internals are initialized
        u = mda.Universe(topo, atom_style='id resid type charge x y z')

        # attach per-atom element attribute if mapping provided
        if type_to_element:
            elements = []
            for atom in u.atoms:
                try:
                    type_id = int(atom.type)
                except Exception:
                    try:
                        type_id = int(str(atom.type))
                    except Exception:
                        type_id = None
                if type_id is not None and type_id in type_to_element:
                    elements.append(type_to_element[type_id])
                else:
                    elements.append('C')
                    print(f"Warning: no element mapping for atom type '{atom.type}' (resolved id {type_id}). Using 'C'.")
            u.add_TopologyAttr('element', values=elements)

        # attach resnames: accept per-residue lists (expand per-residue)
        if resnames is not None:
            u.add_TopologyAttr('resnames', values=resnames)

        u.load_new(traj, format="LAMMPSDUMP", timeunit="fs", dt=dt)

        print(f'box dimensions: {u.dimensions}')
        print(f'frame num: {u.trajectory.n_frames}')

        # convert the Universe instance to Trajectory to preserve MDAnalysis initialization
        u.__class__ = cls
        return u

    def write_xyz(self, connect=False, charge=False, start=0, stop=-1, step=1, dir='.'):
        """
        Write MDAnalysis universe into xyz file, box size into file, and/or connect, charge information.

        Parameters
        ----------
        connect : bool, optional
            Whether to write connectivity information (default: False)
        charge : bool, optional
            Whether to write charge information (default: False)
        step : int, optional
            Step size for trajectory frames (default: 1)
        dir : str, optional
            Output directory path (default: '.')
        """
        # ensure output directory exists and use Path for robust path joining
        output_dir = Path(dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        boxes = []
        if charge:
            charges = []

        if stop == -1:
            stop = self.trajectory.n_frames
        with mda.Writer(str(output_dir / "result_atoms.xyz"), self.atoms.n_atoms) as XYZ:
            self.trajectory[0]
            for ts in self.trajectory[start:stop:step]:
                XYZ.write(self.atoms)
                boxes.append(np.copy(self.dimensions[0:3]))
                if charge:
                    charges += list(self.atoms.charges)

        # boxes
        np.savetxt(str(output_dir / 'result_box.dat'), np.array(boxes), fmt='%12.6f %12.6f %12.6f', comments='')

        # charges
        if charge:
            np.savetxt(str(output_dir / 'result_charge.dat'), np.array(charges)[:, None], comments='')

        if connect:
            with open(str(output_dir / "result_connect.dat"), 'w') as f:
                for i in range(self.atoms.n_atoms):
                    sel = self.select_atoms('index %d' % i)
                    connect_list = ['%s' % sel.atoms[0].id]
                    for bd in sel.bonds:
                        if bd.atoms[0].id == sel.atoms[0].id:
                            connect_list.append('%s' % bd.atoms[1].id)
                        else:
                            connect_list.append('%s' % bd.atoms[0].id)
                    f.write('CONECT ' + ' '.join(connect_list) + '\n')
        return


def move_origin_to_corner(ts):
    ts.positions += ts.dimensions[:3] / 2
    return ts


def move_origin_to_center(ts):
    ts.positions -= ts.dimensions[:3] / 2
    return ts


def get_type_element_map(lmp_datafile):
    """
    Parse LAMMPS data file created by msxbox and return a dict mapping:
      { type_id (int) : element_symbol (str) }
    Behavior:
      - require 'Masses' section
      - require at least one '#' comment in Masses block (else raise)
      - use first alphabetic sequence in the comment: try 2-char then 1-char match
      - fallback to 'C' and print a warning when unable to match
    """
    el_names = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Th', 'Pa', 'U']
    try:
        with open(lmp_datafile, 'r') as fh:
            lines = fh.readlines()
    except Exception as e:
        raise ValueError(f"Unable to read LAMMPS data file '{lmp_datafile}': {e}")
    # locate Masses
    start = None
    for idx, ln in enumerate(lines):
        if ln.strip().lower().startswith('masses'):
            start = idx + 1
            break
    if start is None:
        raise ValueError(f"No 'Masses' section found in {lmp_datafile}")
    # advance to first entry
    i = start
    n = len(lines)
    while i < n and lines[i].strip() == '':
        i += 1
    found_hash = False
    type_to_element = {}
    # parse until blank or next section
    while i < n:
        raw = lines[i]
        line = raw.strip()
        if line == '':
            break
        if line.lstrip().startswith('#'):
            i += 1
            continue
        if not line[0].isdigit():
            break
        parts = raw.split('#', 1)
        data = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ''
        if '#' in raw:
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
            m = re.search(r'[A-Za-z]+', comment)
            if m:
                seq = m.group(0)
                # prefer first two chars (capitalized properly), then first char
                if len(seq) >= 2:
                    cand2 = seq[:2].capitalize()
                    if cand2 in el_names:
                        symbol = cand2
                if symbol is None:
                    cand1 = seq[0].upper()
                    if cand1 in el_names:
                        symbol = cand1
        if symbol is None:
            symbol = 'C'
            print(f"Warning: could not determine element for type {type_id} from comment '{comment}'. Using 'C'.")
        type_to_element[int(type_id)] = symbol
        i += 1
    if not found_hash:
        raise ValueError(f"No '#' comment found in Masses section of {lmp_datafile}; cannot determine element mapping.")
    if len(type_to_element) == 0:
        raise ValueError(f"No mass entries parsed from 'Masses' in {lmp_datafile}")
    return type_to_element


def read_result_thermo(filename="log.lammps", segment=-1):
    """Read thermo table(s) from a LAMMPS log (default ``log.lammps``).

    Expects ``thermo_style custom`` blocks whose header line starts with ``Step``
    (LAMMPS log format). Setup text above/between blocks is ignored.

    Parameters
    ----------
    filename : str or Path
        Path to the LAMMPS log file.
    segment : int or None, default -1
        Which thermo block to return when the log contains several (minimize,
        multiple ``run``, etc.):

        - ``-1``: last block only (typical production segment)
        - ``0, 1, ...``: that block (0-based)
        - ``None``: all blocks concatenated; adds an integer column ``segment``

    Returns
    -------
    pandas.DataFrame
        Normalized lowercase column names. ``v_fluid_temp`` / ``c_fluid_temp``
        become ``temp`` when present.
    """
    import io
    import pandas as pd

    path = Path(filename)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)

    header_idxs = [
        i for i, line in enumerate(lines) if line.lstrip().startswith("Step")
    ]
    if not header_idxs:
        raise ValueError(
            f"No LAMMPS thermo header (line starting with 'Step') in {path}"
        )

    def _parse_block(header_i: int) -> "pd.DataFrame":
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
        if "fluid_temp" in frame.columns and "temp" not in frame.columns:
            frame = frame.rename(columns={"fluid_temp": "temp"})
        return frame

    frames = [_parse_block(i) for i in header_idxs]
    frames = [f for f in frames if not f.empty]
    if not frames:
        raise ValueError(f"Thermo header(s) found but no data rows in {path}")

    if segment is None:
        out = []
        for seg_id, frame in enumerate(frames):
            part = frame.copy()
            part.insert(0, "segment", seg_id)
            out.append(part)
        return pd.concat(out, ignore_index=True)

    n = len(frames)
    idx = segment if segment >= 0 else segment + n
    if idx < 0 or idx >= n:
        raise IndexError(
            f"segment={segment} out of range; log has {n} thermo block(s)"
        )
    return frames[idx].reset_index(drop=True)

"""Render one MDAnalysis frame with fresnel (adapted from mdtoolkit).

Reference:
https://github.com/yaweiliu/mdtoolkit/blob/master/mdtoolkit/visulisation/_render_by_fresnel.py

Typical use in the C04 notebook::

    from _render_by_fresnel import render_universe_frame

    render_universe_frame(
        u_view, frame=-1, outfile="fresnel_last.png",
        color_method="mol", view="ISO",
    )
"""

from __future__ import annotations

__version__ = "1.0.0"
__date__ = "2026-08-01"

from pathlib import Path

import fresnel
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def _truncate_colormap(cmap, minval=0.0, maxval=1.0, n=1000):
    return mpl.colors.LinearSegmentedColormap.from_list(
        f"trunc({cmap.name},{minval:.2f},{maxval:.2f})",
        cmap(np.linspace(minval, maxval, n)),
    )


class _ColorSettings:
    def __init__(self):
        cmap = _truncate_colormap(plt.cm.viridis, 0.35, 0.95)
        self.mapper = mpl.cm.ScalarMappable(
            norm=mpl.colors.Normalize(vmin=0, vmax=1, clip=True),
            cmap=cmap,
        )
        self.blue = fresnel.color.linear(mpl.colors.to_rgba("tab:blue")) * 1.5
        self.grey = fresnel.color.linear(mpl.colors.to_rgba("tab:grey")) * 1.5


_COLORS = _ColorSettings()


def _resolve_frame(universe, frame: int) -> int:
    n = len(universe.trajectory)
    if n < 1:
        raise ValueError("empty trajectory")
    if frame is None or int(frame) < 0:
        return n - 1
    frame_i = int(frame)
    if frame_i >= n:
        raise ValueError(f"frame={frame_i} out of range; n_frames={n}")
    return frame_i


def _wrapped_centered_positions(universe) -> tuple[np.ndarray, np.ndarray]:
    """Wrap by residue (keep each rod intact), then center the box at the origin.

    Per-atom wrap splits rods that straddle a periodic boundary.  Match the
    notebook nglview path: shift origin to the box corner →
    ``AtomGroup.wrap(..., compound="residues")`` → shift back so the box
    center is at the origin for fresnel.  Does not mutate the Universe.
    """
    ts = universe.trajectory.ts
    dims = np.asarray(ts.dimensions[:3], dtype=float)
    pos0 = np.asarray(universe.atoms.positions, dtype=float).copy()
    # LAMMPS / this tutorial: coordinates are box-centered; MDA wrap expects
    # the primary cell with origin at the lower corner.
    universe.atoms.positions = pos0 + 0.5 * dims
    # center='cog': equal-mass beads; avoids requiring masses (com does)
    pos = np.asarray(
        universe.atoms.wrap(compound="residues", center="cog", inplace=False),
        dtype=float,
    )
    universe.atoms.positions = pos0
    pos -= 0.5 * dims
    return pos, dims


def _make_mapper(cmap="viridis", cmap_range=(0.35, 0.95)):
    """Build a ScalarMappable from a (possibly truncated) matplotlib colormap."""
    base = plt.get_cmap(cmap)
    lo, hi = float(cmap_range[0]), float(cmap_range[1])
    trunc = _truncate_colormap(base, lo, hi)
    return mpl.cm.ScalarMappable(
        norm=mpl.colors.Normalize(vmin=0, vmax=1, clip=True),
        cmap=trunc,
    )


def _scalar_colors(
    values: np.ndarray,
    color_threshold=None,
    *,
    cmap="viridis",
    cmap_range=(0.35, 0.95),
):
    values = np.asarray(values, dtype=float)
    if color_threshold is None:
        vmin = float(np.nanmin(values))
        vmax = float(np.nanmax(values))
    else:
        vmin, vmax = float(color_threshold[0]), float(color_threshold[1])
    if vmin == vmax:
        scale = np.full(values.shape, 0.5, dtype=float)
    else:
        scale = (values - vmin) / (vmax - vmin)
        scale = np.clip(scale, 0.0, 1.0)
    mapper = _make_mapper(cmap=cmap, cmap_range=cmap_range)
    rgba = mapper.to_rgba(scale)
    colors = np.array([fresnel.color.linear(c) for c in rgba])
    return colors, vmin, vmax


def render_universe_frame(
    universe,
    frame: int = -1,
    *,
    outfile: str | Path = "fresnel_frame.png",
    nobox: bool = False,
    height: float | None = None,
    view: str = "ISO",
    color_method: str = "mol",
    color_props=None,
    color_threshold=None,
    cmap: str = "viridis",
    cmap_range: tuple[float, float] = (0.35, 0.95),
    radius: float = 0.5,
    size: tuple[int, int] = (600, 600),
    samples: tuple[int, int] = (64, 32),
    device_mode: str = "cpu",
):
    """Path-trace one frame and save a PNG.

    Parameters
    ----------
    universe :
        MDAnalysis Universe (coordinates may be unwrapped; display wrap is
        per residue / rod via ``compound="residues"``, then centered).
    frame :
        Frame index; ``-1`` = last frame.
    outfile :
        Output PNG path.
    nobox :
        If True, do not draw the simulation box.
    height :
        Orthographic camera height; default ``1.2 * |L|``.
    view :
        ``ISO`` / ``X`` / ``-X`` / ``Y`` / ``-Y`` / ``Z`` / ``-Z``.
    color_method :
        ``atom_type`` | ``mol`` | ``atom_props``.
        For ``atom_props``, pass per-atom ``color_props`` (length = n_atoms).
    color_props :
        Per-atom scalars when ``color_method='atom_props'``.
    color_threshold :
        Optional ``(vmin, vmax)`` for the color scale.
    cmap :
        Matplotlib colormap name (e.g. ``viridis``, ``bwr``).
    cmap_range :
        Truncate colormap to ``[lo, hi]`` in colormap coordinates
        (e.g. ``bwr`` with ``(0.3, 0.7)`` avoids deep blue / deep red).
    radius :
        Sphere radius (lj σ/2 = 0.5 for this tutorial).
    size :
        Image ``(width, height)`` in pixels.
    samples :
        ``(path_samples, light_samples)`` for ``Path.sample``.
    device_mode :
        Fresnel device mode (``cpu`` / ``gpu`` if available).

    Returns
    -------
    pathlib.Path
        Path of the written PNG.
    """
    frame_i = _resolve_frame(universe, frame)
    universe.trajectory[frame_i]
    positions, dims = _wrapped_centered_positions(universe)
    n_atoms = positions.shape[0]

    if color_method == "atom_type":
        props = np.asarray(universe.atoms.types, dtype=float)
    elif color_method == "mol":
        # resid ≈ LAMMPS mol id
        props = np.asarray(universe.atoms.resids, dtype=float)
    elif color_method == "atom_props":
        if color_props is None:
            raise ValueError("color_method='atom_props' requires color_props")
        props = np.asarray(color_props, dtype=float)
        if props.shape[0] != n_atoms:
            raise ValueError(
                f"color_props length {props.shape[0]} != n_atoms {n_atoms}"
            )
    else:
        raise ValueError(
            "Unrecognized color_method. "
            "Supported: 'atom_type', 'mol', 'atom_props'"
        )

    colors, vmin, vmax = _scalar_colors(
        props,
        color_threshold=color_threshold,
        cmap=cmap,
        cmap_range=cmap_range,
    )
    print(
        f"Render by fresnel... frame={frame_i}, "
        f"color scale: {vmin:g} {vmax:g}, cmap={cmap}{tuple(cmap_range)}"
    )

    device = fresnel.Device(mode=device_mode)
    path_tracer = fresnel.tracer.Path(device, int(size[0]), int(size[1]))
    scene = fresnel.Scene(device)
    scene.lights = fresnel.light.lightbox()
    scene.background_color = (1, 1, 1)
    scene.background_alpha = 0.0

    geom = fresnel.geometry.Sphere(
        scene, position=positions, radius=float(radius), N=n_atoms
    )
    geom.material = fresnel.material.Material(
        solid=0.0,
        color=_COLORS.blue,
        primitive_color_mix=1.0,
        specular=0.5,
        roughness=0.2,
    )
    geom.color[:] = colors

    box_len = float(np.linalg.norm(dims))
    if height is None:
        height = box_len * 1.2

    if not nobox:
        # fresnel Box: [Lx, Ly, Lz, xy, xz, yz] (centered)
        fresnel.geometry.Box(
            scene,
            [dims[0], dims[1], dims[2], 0.0, 0.0, 0.0],
            box_radius=height / 300.0,
            box_color=_COLORS.grey,
        )

    view = str(view).upper()
    if view == "ISO":
        camera_position = (height, height, height)
        camera_up = (0, 1, 0)
    elif view == "X":
        camera_position = (height, 0, 0)
        camera_up = (0, 1, 0)
    elif view == "-X":
        camera_position = (-height, 0, 0)
        camera_up = (0, 1, 0)
    elif view == "Y":
        camera_position = (0, height, 0)
        camera_up = (1, 0, 0)
    elif view == "-Y":
        camera_position = (0, -height, 0)
        camera_up = (1, 0, 0)
    elif view == "Z":
        camera_position = (0, 0, height)
        camera_up = (0, 1, 0)
    elif view == "-Z":
        camera_position = (0, 0, -height)
        camera_up = (0, 1, 0)
    else:
        raise ValueError(f"Unrecognized view={view!r}")

    scene.camera = fresnel.camera.Orthographic(
        position=camera_position,
        look_at=(0, 0, 0),
        up=camera_up,
        height=height,
    )

    image = path_tracer.sample(
        scene, samples=int(samples[0]), light_samples=int(samples[1])
    )
    out = Path(outfile)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image[:, :, 0:4], mode="RGBA").save(out)
    print(f"saved: {out.resolve()}")
    return out


def color_props_rod_alignment(
    universe,
    *,
    n_beads: int = 11,
    n_hat=None,
) -> np.ndarray:
    """Per-atom color = $|\\hat u \\cdot \\hat n|$ of that atom's rod.

    If ``n_hat`` is None, use the instantaneous nematic director of the frame.
    """
    from _nematic_order import rod_unit_vectors, s2_from_directors

    pos = np.asarray(universe.atoms.positions, dtype=float)
    directors = rod_unit_vectors(pos, n_beads=n_beads)
    if n_hat is None:
        _, n_hat = s2_from_directors(directors)
    n_hat = np.asarray(n_hat, dtype=float)
    align = np.abs(directors @ n_hat)
    # broadcast rod scalar → each bead
    return np.repeat(align, int(n_beads))


def render_snapshot_series(
    universe,
    *,
    outdir: str | Path = "snapshots",
    n_frames: int = 10,
    stride: int = 50,
    start: int = 0,
    color_method: str = "mol",
    n_beads: int = 11,
    prefix: str = "snap",
    **kwargs,
) -> list[Path]:
    """Render ``n_frames`` snapshots every ``stride`` frames into ``outdir``.

    Frame indices: ``start, start+stride, …`` (length ``n_frames``).
    For ``color_method='atom_props'`` with rod alignment, pass nothing in
    ``color_props`` — alignment is recomputed per frame.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    n_traj = len(universe.trajectory)
    frames = [int(start) + i * int(stride) for i in range(int(n_frames))]
    for f in frames:
        if f < 0 or f >= n_traj:
            raise ValueError(
                f"frame {f} out of range; trajectory has {n_traj} frames "
                f"(start={start}, stride={stride}, n_frames={n_frames})"
            )

    # lock camera height from the first snapshot box so the series is comparable
    universe.trajectory[frames[0]]
    dims0 = np.asarray(universe.trajectory.ts.dimensions[:3], dtype=float)
    height = kwargs.pop("height", None)
    if height is None:
        height = float(np.linalg.norm(dims0)) * 1.2

    use_align = color_method == "atom_props" and kwargs.get("color_props") is None
    paths: list[Path] = []
    for f in frames:
        extras = dict(kwargs)
        if use_align:
            universe.trajectory[f]
            extras["color_props"] = color_props_rod_alignment(
                universe, n_beads=n_beads
            )
            extras.setdefault("cmap", "bwr")
            extras.setdefault("cmap_range", (0.3, 0.7))
            extras.setdefault("color_threshold", (0.0, 1.0))
        out = outdir / f"{prefix}_f{f:04d}.png"
        paths.append(
            render_universe_frame(
                universe,
                frame=f,
                outfile=out,
                color_method=color_method,
                height=height,
                **extras,
            )
        )
    print(f"saved {len(paths)} snapshots → {outdir.resolve()}")
    return paths

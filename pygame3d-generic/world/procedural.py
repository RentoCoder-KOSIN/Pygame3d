"""
pygame3d.world.procedural
~~~~~~~~~~~~~~~~~~~~~~~~~
Procedural world-layout generators.

``generate_grid_world`` – places :class:`~pygame3d.world.volume.BoxVolume`
objects and :class:`~pygame3d.world.road.Road` segments on a regular grid.
It is intentionally generic: the caller controls sizes, density, and colours
so the same function works for city blocks, dungeon rooms, forest clearings,
space stations, etc.

Examples
--------
>>> from pygame3d.world.procedural import generate_grid_world
>>>
>>> # city-like layout
>>> volumes, roads = generate_grid_world(
...     map_size=40, block_size=8, density=0.7, seed=42,
...     volume_colors=[[0.7, 0.7, 0.8], [0.8, 0.7, 0.6], [0.9, 0.8, 0.7]],
... )
>>>
>>> # dungeon rooms
>>> rooms, corridors = generate_grid_world(
...     map_size=20, block_size=5, density=0.5, seed=7,
...     height_range=(2.5, 2.5),
...     road_width=1.5,
... )
"""
from __future__ import annotations

import math
import random
from .volume import BoxVolume
from .road import Road


def generate_grid_world(
    map_size: int = 40,
    block_size: int = 8,
    density: float = 0.7,
    seed: int | None = None,
    *,
    height_range: tuple[float, float] = (3.0, 20.0),
    height_weights: list[tuple[float, float]] | None = None,
    width_range: tuple[float, float] = (3.0, 7.0),
    depth_range: tuple[float, float] = (3.0, 7.0),
    road_width: float = 3.0,
    road_color: list[float] | None = None,
    volume_colors: list[list[float]] | None = None,
    entrance_side: str | None = None,
) -> tuple[list[BoxVolume], list[Road]]:
    """Generate a grid-based world layout.

    Parameters
    ----------
    map_size:
        Half-extent of the world.  Actual world = ``map_size * 2`` on each axis.
    block_size:
        Grid spacing between volume cells.
    density:
        Probability (0–1) that a grid cell spawns a volume.
    seed:
        Random seed for reproducible layouts.  ``None`` = random each call.
    height_range:
        ``(min_h, max_h)`` — volume height drawn from *height_weights* if given,
        otherwise uniformly from this range.
    height_weights:
        ``[(height, weight), …]`` for weighted random height selection.
        Overrides *height_range* when provided.
    width_range:
        ``(min_w, max_w)`` horizontal extent on X.
    depth_range:
        ``(min_d, max_d)`` horizontal extent on Z.
    road_width:
        Width of generated road segments.
    road_color:
        Override default road colour.
    volume_colors:
        List of ``[r, g, b]`` palettes to randomly pick from.
    entrance_side:
        Passed to every :class:`~pygame3d.world.volume.BoxVolume` as its
        ``entrance_side``.  ``None`` = solid (no entrance).

    Returns
    -------
    (volumes, roads)
        Two lists ready for rendering and physics.
    """
    if seed is not None:
        random.seed(seed)

    volumes: list[BoxVolume] = []
    roads:   list[Road]     = []

    road_spacing = block_size + 2
    half = map_size // 2

    # ── road grid ─────────────────────────────────────────────────────────────
    for i in range(-half, half + 1, road_spacing):
        roads.append(Road(-map_size, i, map_size, i, width=road_width,
                          color=road_color))
        roads.append(Road(i, -map_size, i, map_size, width=road_width,
                          color=road_color))

    # ── heights ───────────────────────────────────────────────────────────────
    if height_weights:
        h_values, h_weights = zip(*height_weights)
    else:
        h_values = h_weights = None

    default_colors = volume_colors or [
        [0.6, 0.6, 0.7],
        [0.7, 0.65, 0.6],
        [0.75, 0.7, 0.6],
    ]

    # ── volume placement ──────────────────────────────────────────────────────
    for gx in range(-half + 2, half - 2, block_size):
        for gz in range(-half + 2, half - 2, block_size):
            # skip cells that lie within road_width/2 of any road centreline
            def _near_road(r: Road) -> bool:
                dx = r.x2 - r.x1
                dz = r.z2 - r.z1
                length = math.sqrt(dx*dx + dz*dz) or 1.0
                # perpendicular distance from (gx, gz) to the road line
                perp = abs(dx * (r.z1 - gz) - dz * (r.x1 - gx)) / length
                return perp < r.width

            on_road = any(_near_road(r) for r in roads)
            if on_road or random.random() >= density:
                continue

            if h_values and h_weights:
                h = random.choices(h_values, weights=h_weights, k=1)[0]
            else:
                h = random.uniform(*height_range)

            w = random.uniform(*width_range)
            d = random.uniform(*depth_range)
            ox = random.uniform(-1.0, 1.0)
            oz = random.uniform(-1.0, 1.0)
            col = random.choice(default_colors)

            volumes.append(BoxVolume(
                gx + ox, 0.0, gz + oz,
                width=w, height=h, depth=d,
                color=col,
                entrance_side=entrance_side,
            ))

    return volumes, roads

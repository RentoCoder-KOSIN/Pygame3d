"""
pygame3d.world.volume
~~~~~~~~~~~~~~~~~~~~~
Generic axis-aligned bounding volumes for static world geometry.

``Volume``    – abstract base (provides collision API).
``BoxVolume`` – solid rectangular box with optional entrance gap.

These replace the old game-specific ``Building`` class with a composable,
genre-neutral collision primitive that any 3-D game can use.

Examples
--------
>>> wall = BoxVolume(0, 0, 0, width=10, height=3, depth=1)
>>> wall.check_collision(px=1, py=1, pz=0, radius=0.5)
True

>>> platform = BoxVolume(5, 2, 5, width=6, height=0.5, depth=6,
...                      color=[0.3, 0.6, 0.3])
"""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Any


class Volume(ABC):
    """Abstract static collision volume."""

    @abstractmethod
    def check_collision(self, px: float, py: float, pz: float, radius: float) -> bool:
        """Return True if the sphere ``(px, py, pz, radius)`` overlaps this volume."""

    @abstractmethod
    def check_inside(self, px: float, py: float, pz: float) -> bool:
        """Return True if point ``(px, py, pz)`` is strictly inside the volume."""


class BoxVolume(Volume):
    """Axis-aligned solid box with optional passable entrance gap.

    Parameters
    ----------
    x, y, z:
        Centre position of the box.
    width:
        Extent on the X axis.
    height:
        Extent on the Y axis.
    depth:
        Extent on the Z axis.
    color:
        ``[r, g, b]`` float list for the renderer.
    entrance_side:
        ``"front"`` (−Z face), ``"back"``, ``"left"``, ``"right"``, or ``None``.
    entrance_width:
        Width of the entrance gap as a fraction of the face width.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        *,
        width: float = 4.0,
        height: float = 3.0,
        depth: float = 4.0,
        color: list[float] | None = None,
        entrance_side: str | None = None,
        entrance_width: float = 0.4,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.width  = width
        self.height = height
        self.depth  = depth
        self.color  = color if color is not None else [0.6, 0.6, 0.65]
        self.id     = random.randint(1000, 9999)

        self.entrance_side  = entrance_side
        self.entrance_width = entrance_width  # fraction

    # ── bounds helpers ────────────────────────────────────────────────────────

    @property
    def min_x(self) -> float: return self.x - self.width  / 2
    @property
    def max_x(self) -> float: return self.x + self.width  / 2
    @property
    def min_y(self) -> float: return self.y
    @property
    def max_y(self) -> float: return self.y + self.height
    @property
    def min_z(self) -> float: return self.z - self.depth  / 2
    @property
    def max_z(self) -> float: return self.z + self.depth  / 2

    # ── collision ─────────────────────────────────────────────────────────────

    def check_collision(self, px: float, py: float, pz: float, radius: float) -> bool:
        """Broad AABB sphere check with optional entrance gap."""
        r = radius
        if not (
            self.min_x - r < px < self.max_x + r
            and self.min_z - r < pz < self.max_z + r
            and self.min_y     < py < self.max_y + r
        ):
            return False
        if self.entrance_side and self._in_entrance(px, py, pz):
            return False
        return True

    def check_inside(self, px: float, py: float, pz: float) -> bool:
        return (
            self.min_x < px < self.max_x
            and self.min_z < pz < self.max_z
            and self.min_y < py < self.max_y
        )

    def _in_entrance(self, px: float, py: float, pz: float) -> bool:
        side = self.entrance_side
        ew   = self.entrance_width
        # front face (−Z)
        if side == "front":
            gap_half = (self.width * ew) / 2
            return abs(px - self.x) < gap_half and pz < self.min_z + 0.5
        if side == "back":
            gap_half = (self.width * ew) / 2
            return abs(px - self.x) < gap_half and pz > self.max_z - 0.5
        if side == "left":
            gap_half = (self.depth * ew) / 2
            return abs(pz - self.z) < gap_half and px < self.min_x + 0.5
        if side == "right":
            gap_half = (self.depth * ew) / 2
            return abs(pz - self.z) < gap_half and px > self.max_x - 0.5
        return False

    def draw(self) -> None:
        """Draw this box (requires PyOpenGL)."""
        try:
            from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glScalef
            from ..render.primitives import draw_cube
        except ImportError:  # pragma: no cover
            return
        glPushMatrix()
        glTranslatef(self.x, self.y + self.height / 2, self.z)
        glScalef(self.width / 2, self.height / 2, self.depth / 2)
        draw_cube(1.0, self.color)
        glPopMatrix()

    def __repr__(self) -> str:
        return (
            f"<BoxVolume id={self.id} "
            f"pos=({self.x:.1f},{self.y:.1f},{self.z:.1f}) "
            f"size=({self.width:.1f}×{self.height:.1f}×{self.depth:.1f})>"
        )

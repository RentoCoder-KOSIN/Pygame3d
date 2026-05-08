"""
pygame3d.world.road
~~~~~~~~~~~~~~~~~~~
A simple road / path segment between two 3-D points.

Can represent roads, rivers, corridors, or any linear world feature.
"""
from __future__ import annotations

import math


class Road:
    """A straight segment connecting ``(x1, z1)`` to ``(x2, z2)``.

    Parameters
    ----------
    x1, z1:
        Start point on the XZ plane.
    x2, z2:
        End point on the XZ plane.
    width:
        Road width in world-units.
    color:
        ``[r, g, b]`` surface colour.
    line_color:
        ``[r, g, b]`` centre-line colour.
    """

    def __init__(
        self,
        x1: float,
        z1: float,
        x2: float,
        z2: float,
        *,
        width: float = 3.0,
        color: list[float] | None = None,
        line_color: list[float] | None = None,
    ) -> None:
        self.x1 = x1
        self.z1 = z1
        self.x2 = x2
        self.z2 = z2
        self.width      = width
        self.color      = color      if color      is not None else [0.2, 0.2, 0.2]
        self.line_color = line_color if line_color is not None else [0.8, 0.8, 0.8]

    @property
    def length(self) -> float:
        return math.dist((self.x1, self.z1), (self.x2, self.z2))

    @property
    def direction(self) -> tuple[float, float]:
        """Normalised ``(dx, dz)`` along the road."""
        dx = self.x2 - self.x1
        dz = self.z2 - self.z1
        l  = math.sqrt(dx*dx + dz*dz) or 1.0
        return (dx / l, dz / l)

    def draw(self, y_offset: float = 0.02) -> None:
        """Draw this road segment (requires PyOpenGL)."""
        try:
            from OpenGL.GL import glBegin, glEnd, glNormal3f, glVertex3f, glColor3fv, GL_QUADS, GL_LINES
        except ImportError:  # pragma: no cover
            return

        dx, dz = self.direction
        px, pz = -dz, dx          # perpendicular
        w2 = self.width / 2
        y  = y_offset

        glColor3fv(self.color)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(self.x1 + px * w2, y, self.z1 + pz * w2)
        glVertex3f(self.x1 - px * w2, y, self.z1 - pz * w2)
        glVertex3f(self.x2 - px * w2, y, self.z2 - pz * w2)
        glVertex3f(self.x2 + px * w2, y, self.z2 + pz * w2)
        glEnd()

        glColor3fv(self.line_color)
        glBegin(GL_LINES)
        glVertex3f(self.x1, y + 0.01, self.z1)
        glVertex3f(self.x2, y + 0.01, self.z2)
        glEnd()

    def __repr__(self) -> str:
        return (
            f"<Road ({self.x1:.1f},{self.z1:.1f})→"
            f"({self.x2:.1f},{self.z2:.1f}) w={self.width}>"
        )

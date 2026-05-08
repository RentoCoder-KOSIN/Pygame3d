"""
pygame3d.render.scene
~~~~~~~~~~~~~~~~~~~~~
Generic scene-level OpenGL draw calls: ground plane, grid, ambient lighting.
"""
from __future__ import annotations

try:
    from OpenGL.GL import (
        glBegin, glEnd, glVertex3f, glNormal3f, glColor3f, glColor3fv,
        GL_QUADS, GL_LINES,
        glLightfv, GL_LIGHT0, GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
        glEnable, GL_LIGHTING, GL_LIGHT0 as _L0, GL_COLOR_MATERIAL,
        GL_DEPTH_TEST, GL_NORMALIZE,
        glColorMaterial, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
    )
    _OPENGL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENGL_AVAILABLE = False


def setup_lighting(
    position: list[float] | None = None,
    ambient: list[float] | None = None,
    diffuse: list[float] | None = None,
) -> None:
    """Configure a single directional light (GL_LIGHT0).

    Call once after creating the OpenGL context.

    Parameters
    ----------
    position:
        ``[x, y, z, w]``.  ``w=0`` → directional, ``w=1`` → point.
        Defaults to overhead-left.
    ambient:
        ``[r, g, b, a]`` ambient intensity.  Default: dim grey.
    diffuse:
        ``[r, g, b, a]`` diffuse intensity.  Default: near-white.
    """
    if not _OPENGL_AVAILABLE:
        return
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)

    pos = position if position is not None else [5.0, 10.0, 5.0, 0.0]
    amb = ambient  if ambient  is not None else [0.3, 0.3, 0.3, 1.0]
    dif = diffuse  if diffuse  is not None else [0.9, 0.9, 0.9, 1.0]

    glLightfv(GL_LIGHT0, GL_POSITION, pos)
    glLightfv(GL_LIGHT0, GL_AMBIENT,  amb)
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  dif)


def draw_ground(
    half_size: float = 40.0,
    color: list[float] | None = None,
) -> None:
    """Draw a flat ground plane centred at the world origin.

    Parameters
    ----------
    half_size:
        Half-extent of the ground quad on X and Z.
    color:
        ``[r, g, b]`` float list.  Defaults to medium grey.
    """
    if not _OPENGL_AVAILABLE:
        return
    c = color if color is not None else [0.35, 0.35, 0.35]
    glColor3fv(c)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-half_size, 0, -half_size)
    glVertex3f( half_size, 0, -half_size)
    glVertex3f( half_size, 0,  half_size)
    glVertex3f(-half_size, 0,  half_size)
    glEnd()


def draw_grid(
    half_size: float = 20.0,
    step: float = 2.0,
    color: list[float] | None = None,
    y_offset: float = 0.01,
) -> None:
    """Draw a reference grid on the XZ plane.

    Parameters
    ----------
    half_size:
        Grid extends from ``-half_size`` to ``+half_size`` on X and Z.
    step:
        Spacing between grid lines.
    color:
        ``[r, g, b]`` float list.  Defaults to dark grey.
    y_offset:
        Vertical offset above the ground to avoid z-fighting.
    """
    if not _OPENGL_AVAILABLE:
        return
    c = color if color is not None else [0.25, 0.25, 0.25]
    glColor3fv(c)
    glBegin(GL_LINES)
    i = -half_size
    while i <= half_size:
        glVertex3f(i,          y_offset, -half_size)
        glVertex3f(i,          y_offset,  half_size)
        glVertex3f(-half_size, y_offset,  i)
        glVertex3f( half_size, y_offset,  i)
        i += step
    glEnd()

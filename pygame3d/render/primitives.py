"""
pygame3d.render.primitives
~~~~~~~~~~~~~~~~~~~~~~~~~~
Low-level OpenGL drawing helpers for common 3-D shapes.

All functions are stateless: they push/pop the matrix stack and restore GL
state so they can be called in any order without side effects.

Requirements: PyOpenGL
"""
from __future__ import annotations

import math

try:
    from OpenGL.GL import (
        glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef,
        glColor3fv, glColor4f, glNormal3fv, glVertex3fv,
        glBegin, glEnd, glEnable, glDisable,
        GL_QUADS, GL_LINES, GL_LIGHTING, GL_LINE_STRIP,
    )
    from OpenGL.GLU import gluNewQuadric, gluDeleteQuadric, gluSphere, gluCylinder
    from OpenGL.GLU import gluDisk, gluQuadricNormals, gluQuadricTexture
    from OpenGL.GLU import GLU_SMOOTH
    _OPENGL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENGL_AVAILABLE = False


def _check() -> None:
    if not _OPENGL_AVAILABLE:
        raise RuntimeError(
            "PyOpenGL is not installed.  Run: pip install PyOpenGL"
        )


# ── primitives ───────────────────────────────────────────────────────────────

def draw_sphere(
    radius: float,
    color: list[float],
    *,
    slices: int = 16,
    stacks: int = 16,
) -> None:
    """Draw a solid sphere centred at the current matrix origin.

    Parameters
    ----------
    radius:
        Sphere radius (world-units).
    color:
        ``[r, g, b]`` float list.
    slices, stacks:
        Tessellation quality.
    """
    _check()
    glColor3fv(color)
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluQuadricTexture(q, False)
    gluSphere(q, radius, slices, stacks)
    gluDeleteQuadric(q)


def draw_cube(
    half_size: float,
    color: list[float] | None = None,
    *,
    wireframe: bool = False,
) -> None:
    """Draw an axis-aligned cube centred at the current matrix origin.

    Parameters
    ----------
    half_size:
        Half-extent on each axis (cube side = ``half_size * 2``).
    color:
        ``[r, g, b]`` float list.  Pass ``None`` to leave GL colour unchanged.
    wireframe:
        If ``True``, draw edges only.
    """
    _check()
    s = half_size
    vertices = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s,  s], [s, -s,  s], [s, s,  s], [-s, s,  s],
    ]
    faces = [
        ([0, 1, 2, 3], [0,  0, -1]),
        ([4, 7, 6, 5], [0,  0,  1]),
        ([0, 4, 5, 1], [0, -1,  0]),
        ([2, 6, 7, 3], [0,  1,  0]),
        ([0, 3, 7, 4], [-1, 0,  0]),
        ([1, 5, 6, 2], [1,  0,  0]),
    ]
    edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]

    if color is not None:
        glColor3fv(color)

    if wireframe:
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        for e in edges:
            for v in e:
                glVertex3fv(vertices[v])
        glEnd()
        glEnable(GL_LIGHTING)
    else:
        glBegin(GL_QUADS)
        for verts, normal in faces:
            glNormal3fv(normal)
            for v in verts:
                glVertex3fv(vertices[v])
        glEnd()


def draw_cylinder(
    radius: float,
    height: float,
    color: list[float],
    *,
    slices: int = 16,
    capped: bool = True,
) -> None:
    """Draw a vertical cylinder centred at the current matrix origin.

    Parameters
    ----------
    radius:
        Cylinder radius.
    height:
        Cylinder height (extends ``height/2`` above and below origin).
    color:
        ``[r, g, b]`` float list.
    slices:
        Tessellation quality.
    capped:
        If ``True``, draw top and bottom discs.
    """
    _check()
    glColor3fv(color)
    glPushMatrix()
    glTranslatef(0, -height / 2, 0)
    glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluCylinder(q, radius, radius, height, slices, 1)
    if capped:
        gluDisk(q, 0, radius, slices, 1)
        glTranslatef(0, 0, height)
        gluDisk(q, 0, radius, slices, 1)
    gluDeleteQuadric(q)
    glPopMatrix()


def draw_character_capsule(
    height: float,
    radius: float,
    color: list[float],
    *,
    rotation: float = 0.0,
) -> None:
    """Draw a capsule-shaped character model (sphere body + sphere head).

    This is a simple stand-in shape for any upright entity.
    Replace with your own model loader for production.

    Parameters
    ----------
    height:
        Total character height.
    radius:
        Bounding radius (used for both body sphere and scaled head).
    color:
        ``[r, g, b]`` float list for the body.
    rotation:
        Y-axis rotation in degrees (character facing direction).
    """
    _check()
    glPushMatrix()
    glRotatef(rotation, 0, 1, 0)

    # body sphere
    glPushMatrix()
    glTranslatef(0, height * 0.3, 0)
    draw_sphere(radius * 0.7, color, slices=12, stacks=12)
    glPopMatrix()

    # head sphere (slightly lighter)
    head_color = [min(1.0, c * 1.2) for c in color]
    glPushMatrix()
    glTranslatef(0, height * 0.8, 0)
    draw_sphere(radius * 0.35, head_color, slices=10, stacks=10)
    glPopMatrix()

    glPopMatrix()

"""
pygame3d.core.camera
~~~~~~~~~~~~~~~~~~~~
First- and third-person camera with smooth following, mouse-look,
and OpenGL projection setup.
"""
from __future__ import annotations

import math


class Camera:
    """3-D camera that can follow a target entity or be moved manually.

    Parameters
    ----------
    fov:
        Vertical field-of-view in degrees.
    near, far:
        Near and far clipping planes.
    distance:
        Third-person follow distance behind the target.
    height_offset:
        Y-offset above the target origin.
    smoothing:
        Interpolation factor (0–1) for position following.
        ``1.0`` = instant snap, ``0.1`` = very smooth.
    """

    def __init__(
        self,
        fov: float = 60.0,
        near: float = 0.1,
        far: float = 500.0,
        *,
        distance: float = 10.0,
        height_offset: float = 3.0,
        smoothing: float = 0.2,
    ) -> None:
        self.fov = fov
        self.near = near
        self.far = far

        # position & orientation
        self.x = 0.0
        self.y = height_offset
        self.z = distance
        self.angle_h = 0.0   # horizontal (yaw) in degrees
        self.angle_v = 20.0  # vertical (pitch) in degrees, clamped

        self.distance = distance
        self.height_offset = height_offset
        self.smoothing = smoothing

        # targets
        self._target_x = 0.0
        self._target_y = 0.0
        self._target_z = 0.0

    # ── mouse-look ───────────────────────────────────────────────────────────

    def rotate(self, dx: float, dy: float, sensitivity: float = 0.3) -> None:
        """Update yaw/pitch from mouse deltas *dx*, *dy*."""
        self.angle_h = (self.angle_h + dx * sensitivity) % 360.0
        self.angle_v = max(-80.0, min(80.0, self.angle_v + dy * sensitivity))

    # ── follow ───────────────────────────────────────────────────────────────

    def follow(self, tx: float, ty: float, tz: float) -> None:
        """Move the camera to orbit the point ``(tx, ty, tz)``."""
        ar_h = math.radians(self.angle_h)
        ar_v = math.radians(self.angle_v)

        dx = math.sin(ar_h) * math.cos(ar_v) * self.distance
        dy = math.sin(ar_v) * self.distance
        dz = math.cos(ar_h) * math.cos(ar_v) * self.distance

        target_x = tx + dx
        target_y = ty + self.height_offset + dy
        target_z = tz + dz

        s = self.smoothing
        self.x += (target_x - self.x) * s
        self.y += (target_y - self.y) * s
        self.z += (target_z - self.z) * s

        self._target_x = tx
        self._target_y = ty + self.height_offset * 0.5
        self._target_z = tz

    # ── OpenGL integration ───────────────────────────────────────────────────

    def apply_projection(self, viewport_w: int, viewport_h: int) -> None:
        """Set up the OpenGL perspective projection matrix."""
        try:
            from OpenGL.GL import glMatrixMode, glLoadIdentity, GL_PROJECTION
            from OpenGL.GLU import gluPerspective
        except ImportError:
            return
        aspect = viewport_w / max(viewport_h, 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, aspect, self.near, self.far)

    def apply_view(self) -> None:
        """Set up the OpenGL modelview matrix (look-at)."""
        try:
            from OpenGL.GL import glMatrixMode, glLoadIdentity, GL_MODELVIEW
            from OpenGL.GLU import gluLookAt
        except ImportError:
            return
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.x, self.y, self.z,
            self._target_x, self._target_y, self._target_z,
            0.0, 1.0, 0.0,
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    @property
    def forward(self) -> tuple[float, float]:
        """``(fx, fz)`` unit vector pointing in the camera's horizontal facing direction."""
        ar = math.radians(self.angle_h)
        return (-math.sin(ar), -math.cos(ar))

    @property
    def right(self) -> tuple[float, float]:
        """``(rx, rz)`` unit vector pointing 90° right of :attr:`forward`."""
        fx, fz = self.forward
        return (-fz, fx)

    def __repr__(self) -> str:
        return (
            f"<Camera pos=({self.x:.1f},{self.y:.1f},{self.z:.1f}) "
            f"angle_h={self.angle_h:.1f} angle_v={self.angle_v:.1f}>"
        )

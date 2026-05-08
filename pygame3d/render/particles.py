"""
pygame3d.render.particles
~~~~~~~~~~~~~~~~~~~~~~~~~
Lightweight CPU particle system with OpenGL point-sprite rendering.

Designed for muzzle flashes, explosions, dust, sparks, magic effects —
anything that requires many small short-lived sprites without a GPU shader.

Usage
-----
>>> ps = ParticleSystem(max_particles=500)
>>> ps.emit(x=0, y=1, z=0, count=30, color=[1.0, 0.4, 0.0])
>>> # per frame:
>>> ps.update()
>>> ps.draw()
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class Particle:
    """Single particle state."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    life: int = 30          # frames remaining
    max_life: int = 30
    size: float = 0.15
    color: list[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    gravity: float = -0.01

    @property
    def alpha(self) -> float:
        return self.life / self.max_life

    def update(self) -> bool:
        """Advance one frame.  Returns True while alive."""
        self.vy += self.gravity
        self.x  += self.vx
        self.y  += self.vy
        self.z  += self.vz
        self.life -= 1
        return self.life > 0


class ParticleSystem:
    """Manages a pool of :class:`Particle` objects.

    Parameters
    ----------
    max_particles:
        Hard cap on simultaneous particles.
    """

    def __init__(self, max_particles: int = 1000) -> None:
        self.max_particles = max_particles
        self._particles: list[Particle] = []

    # ── emit ─────────────────────────────────────────────────────────────────

    def emit(
        self,
        x: float,
        y: float,
        z: float,
        *,
        count: int = 10,
        color: list[float] | None = None,
        speed: float = 0.1,
        speed_spread: float = 0.05,
        life: int = 40,
        life_spread: int = 15,
        size: float = 0.15,
        gravity: float = -0.01,
        direction: tuple[float, float, float] | None = None,
        spread_angle: float = 180.0,
    ) -> None:
        """Spawn *count* particles at position ``(x, y, z)``.

        Parameters
        ----------
        count:
            Number of particles to spawn.
        color:
            Base ``[r, g, b]`` colour.  Each particle gets a slight variation.
        speed:
            Mean initial speed.
        speed_spread:
            ± random speed variance.
        life:
            Mean lifetime in frames.
        life_spread:
            ± random lifetime variance.
        size:
            Particle sphere radius.
        gravity:
            Per-frame downward acceleration.
        direction:
            If set, particles spread within *spread_angle* around this vector.
            ``None`` = full sphere emission.
        spread_angle:
            Half-angle (degrees) of the emission cone when *direction* is set.
        """
        base_color = color if color is not None else [1.0, 1.0, 1.0]
        slots_left = self.max_particles - len(self._particles)
        n = min(count, slots_left)

        for _ in range(n):
            if direction is not None:
                vx, vy, vz = self._cone_dir(direction, spread_angle)
            else:
                vx, vy, vz = self._sphere_dir()

            sp = max(0.0, speed + random.uniform(-speed_spread, speed_spread))
            lf = max(1, life + random.randint(-life_spread, life_spread))
            col = [min(1.0, max(0.0, c + random.uniform(-0.1, 0.1))) for c in base_color]

            self._particles.append(Particle(
                x=x, y=y, z=z,
                vx=vx * sp, vy=vy * sp, vz=vz * sp,
                life=lf, max_life=lf,
                size=size, color=col, gravity=gravity,
            ))

    # ── update / draw ─────────────────────────────────────────────────────────

    def update(self) -> None:
        """Advance all particles one frame and prune dead ones."""
        self._particles = [p for p in self._particles if p.update()]

    def draw(self) -> None:
        """Draw all particles as small spheres (requires PyOpenGL)."""
        try:
            from OpenGL.GL import (
                glPushMatrix, glPopMatrix, glTranslatef, glColor4f,
                glEnable, glDisable, GL_BLEND, GL_SRC_ALPHA,
                GL_ONE_MINUS_SRC_ALPHA, glBlendFunc,
            )
            from .primitives import draw_sphere
        except ImportError:  # pragma: no cover
            return

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for p in self._particles:
            glPushMatrix()
            glTranslatef(p.x, p.y, p.z)
            glColor4f(*p.color, p.alpha)
            draw_sphere(p.size, p.color, slices=6, stacks=6)
            glPopMatrix()
        glDisable(GL_BLEND)

    @property
    def count(self) -> int:
        """Number of active particles."""
        return len(self._particles)

    def clear(self) -> None:
        """Remove all particles."""
        self._particles.clear()

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _sphere_dir() -> tuple[float, float, float]:
        theta = random.uniform(0, 2 * math.pi)
        phi   = random.uniform(0, math.pi)
        return (
            math.sin(phi) * math.cos(theta),
            math.cos(phi),
            math.sin(phi) * math.sin(theta),
        )

    @staticmethod
    def _cone_dir(
        direction: tuple[float, float, float],
        half_angle_deg: float,
    ) -> tuple[float, float, float]:
        ha = math.radians(half_angle_deg)
        dx, dy, dz = direction
        length = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        dx, dy, dz = dx/length, dy/length, dz/length

        theta = random.uniform(0, 2 * math.pi)
        phi   = random.uniform(0, ha)
        # random vector in cone aligned with +Y then rotate to direction
        sx = math.sin(phi) * math.cos(theta)
        sy = math.cos(phi)
        sz = math.sin(phi) * math.sin(theta)

        # Simple rotation: if direction ≈ +Y, skip rotation
        if abs(dy) > 0.999:
            return (sx * math.copysign(1, dy), sy * math.copysign(1, dy), sz)

        # Rodrigues rotation to align +Y → direction
        ux, uy, uz = -dz, 0.0, dx   # cross(+Y, dir) unnormalised
        ul = math.sqrt(ux*ux + uz*uz) or 1.0
        ux, uz = ux/ul, uz/ul
        angle = math.acos(max(-1.0, min(1.0, dy)))
        c, s = math.cos(angle), math.sin(angle)
        rx = (c + ux*ux*(1-c))*sx +    (-uz*s)*sy + (ux*uz*(1-c))*sz
        ry =        (uz*s)*sx + c*sy +     (-ux*s)*sz
        rz = (ux*uz*(1-c))*sx +    (ux*s)*sy + (c + uz*uz*(1-c))*sz
        return (rx, ry, rz)

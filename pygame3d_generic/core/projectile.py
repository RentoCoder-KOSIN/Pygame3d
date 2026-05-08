"""
pygame3d.core.projectile
~~~~~~~~~~~~~~~~~~~~~~~~
Generic projectile supporting straight travel, homing, and area-of-effect.

This module has *no* game-specific logic (weapons, triggers, combat systems).
It models a flying object that can detect overlap with any positioned objects
and optionally home toward the nearest alive target.
"""
from __future__ import annotations

import math
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Positionable(Protocol):
    """Minimal interface for homing / collision targets."""

    x: float
    y: float
    z: float
    size: float
    is_alive: bool


class Projectile:
    """A flying object with optional homing and AoE detection.

    Parameters
    ----------
    x, y, z:
        Spawn position.
    direction:
        ``(dx, dz)`` — a 2-D horizontal unit vector (auto-normalised).
    speed:
        World-units per frame.
    damage:
        Logical damage value carried by this projectile (applied by caller).
    owner:
        Opaque reference to the firing entity.  Useful for hit filtering.
    size:
        Collision sphere radius.
    color:
        ``[r, g, b]`` float list for the renderer.
    is_homing:
        If ``True``, steer toward the nearest ``Positionable`` in *targets*.
    explosion_radius:
        If > 0, :meth:`get_aoe_targets` returns all targets within this radius.
    lifetime:
        Frames until the projectile expires.
    world_bounds:
        ``(half_x, half_z)`` — projectile is removed outside this box.

    Examples
    --------
    >>> proj = Projectile(0, 1, 0, direction=(1, 0), speed=0.8, damage=25)
    >>> alive = proj.update(targets=[enemy])
    >>> if proj.check_collision(enemy):
    ...     enemy.take_damage(proj.damage)
    """

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        direction: tuple[float, float],
        *,
        speed: float = 0.5,
        damage: int = 10,
        owner: Any = None,
        size: float = 0.2,
        color: list[float] | None = None,
        is_homing: bool = False,
        explosion_radius: float = 0.0,
        lifetime: int = 180,
        world_bounds: tuple[float, float] = (50.0, 50.0),
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.size = size
        self.color: list[float] = color if color is not None else [1.0, 0.5, 0.0]
        self.is_homing = is_homing
        self.explosion_radius = explosion_radius
        self.lifetime = lifetime
        self.world_bounds = world_bounds

        # normalise direction
        dx, dz = direction
        length = math.sqrt(dx * dx + dz * dz) or 1.0
        self.direction: tuple[float, float] = (dx / length, dz / length)

        self._tracking_target: Any | None = None
        self.is_alive = True

    # ── update ───────────────────────────────────────────────────────────────

    def update(self, targets: list | None = None) -> bool:
        """Advance one frame.

        Parameters
        ----------
        targets:
            List of objects to consider for homing.  Ignored when
            :attr:`is_homing` is ``False``.

        Returns
        -------
        bool
            ``True`` while the projectile is alive.
        """
        if self.is_homing and targets:
            self._steer(targets)

        self.x += self.direction[0] * self.speed
        self.z += self.direction[1] * self.speed
        self.lifetime -= 1

        bx, bz = self.world_bounds
        if abs(self.x) > bx or abs(self.z) > bz or self.lifetime <= 0:
            self.is_alive = False

        return self.is_alive

    def _steer(self, targets: list) -> None:
        """Lock on to the nearest alive target and steer toward it."""
        if not self._tracking_target:
            best_d = float("inf")
            for t in targets:
                if isinstance(t, Positionable) and t.is_alive:
                    d = math.dist((self.x, self.y, self.z), (t.x, t.y, t.z))
                    if d < best_d:
                        best_d = d
                        self._tracking_target = t

        if self._tracking_target and isinstance(self._tracking_target, Positionable):
            dx = self._tracking_target.x - self.x
            dz = self._tracking_target.z - self.z
            dist = math.sqrt(dx * dx + dz * dz)
            if dist > 0.1:
                self.direction = (dx / dist, dz / dist)
            else:
                self._tracking_target = None

    # ── collision ────────────────────────────────────────────────────────────

    def check_collision(self, target: Any) -> bool:
        """Return ``True`` if this projectile's sphere overlaps *target*."""
        if not (hasattr(target, "x") and hasattr(target, "size")):
            return False
        d = math.dist(
            (self.x, self.y, self.z),
            (target.x, getattr(target, "y", self.y), target.z),
        )
        return d < (self.size + target.size)

    def get_aoe_targets(self, targets: list, radius: float | None = None) -> list:
        """Return all targets within *radius* (defaults to :attr:`explosion_radius`).

        Parameters
        ----------
        targets:
            Candidate objects (must have ``x``, ``z`` attributes).
        radius:
            Override for the explosion radius.
        """
        r = radius if radius is not None else self.explosion_radius
        result = []
        for t in targets:
            if hasattr(t, "x"):
                d = math.dist(
                    (self.x, self.y, self.z),
                    (t.x, getattr(t, "y", self.y), t.z),
                )
                if d <= r:
                    result.append(t)
        return result

    def __repr__(self) -> str:
        return (
            f"<Projectile pos=({self.x:.1f},{self.y:.1f},{self.z:.1f}) "
            f"speed={self.speed} lifetime={self.lifetime}>"
        )

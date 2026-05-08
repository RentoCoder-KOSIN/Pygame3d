"""
pygame3d.core.entity
~~~~~~~~~~~~~~~~~~~~
Base classes for all game objects.

``Entity``        – static, positioned object (building, prop, collectable …)
``DynamicEntity`` – entity that moves, has velocity and health.
"""
from __future__ import annotations

import math
from typing import Any


class Entity:
    """Minimal positioned object.

    All game objects (static or dynamic) share this interface so that
    physics, rendering and networking can treat them uniformly.

    Parameters
    ----------
    x, y, z:
        Initial world-space position.
    size:
        Bounding-sphere radius used for broad-phase collision.
    color:
        ``[r, g, b]`` float list (0–1). Passed straight to the renderer.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        *,
        size: float = 0.5,
        color: list[float] | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.color: list[float] = color if color is not None else [1.0, 1.0, 1.0]
        self.id: int = 0  # assigned by the scene / world manager

    # ── convenience ──────────────────────────────────────────────────────────

    def get_pos(self) -> tuple[float, float, float]:
        """Return current position as ``(x, y, z)``."""
        return (self.x, self.y, self.z)

    def set_pos(self, x: float, y: float, z: float) -> None:
        """Teleport to ``(x, y, z)``."""
        self.x, self.y, self.z = x, y, z

    def distance_to(self, other: "Entity") -> float:
        """Euclidean distance to *other*."""
        return math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))

    def overlaps(self, other: "Entity") -> bool:
        """Sphere-sphere overlap test."""
        return self.distance_to(other) < (self.size + other.size)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Override to add per-frame logic."""

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} "
            f"pos=({self.x:.2f},{self.y:.2f},{self.z:.2f})>"
        )


class DynamicEntity(Entity):
    """Entity with velocity, gravity, and hit-points.

    Parameters
    ----------
    x, y, z:
        Spawn position.
    size:
        Bounding-sphere radius.
    color:
        ``[r, g, b]`` float list.
    max_health:
        Starting and maximum HP.  Set to ``None`` for indestructible objects.
    speed:
        Base movement speed (world-units / frame).
    gravity:
        Downward acceleration applied each frame.  ``0`` disables gravity.
    world_bounds:
        ``(half_x, half_z)`` box that clamps horizontal position.
        ``None`` means unbounded.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        *,
        size: float = 0.5,
        color: list[float] | None = None,
        max_health: int | None = 100,
        speed: float = 0.1,
        gravity: float = -0.02,
        world_bounds: tuple[float, float] | None = (25.0, 25.0),
    ) -> None:
        super().__init__(x, y, z, size=size, color=color)
        self.vx = self.vy = self.vz = 0.0
        self.speed = speed
        self.gravity = gravity
        self.on_ground = False
        self.world_bounds = world_bounds
        self.rotation = 0.0

        # health
        self.max_health: int | None = max_health
        self.health: int = max_health if max_health is not None else 0
        self.is_alive = True

    # ── physics step ─────────────────────────────────────────────────────────

    def apply_gravity(self) -> None:
        """Apply gravity and clamp to ground (y = size)."""
        if self.gravity == 0:
            return
        self.vy += self.gravity
        self.y += self.vy
        if self.y <= self.size:
            self.y = self.size
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

    def apply_velocity(self) -> None:
        """Integrate velocity into position and enforce world bounds."""
        self.x += self.vx
        self.z += self.vz
        if self.world_bounds:
            bx, bz = self.world_bounds
            if abs(self.x) > bx:
                self.x = math.copysign(bx, self.x)
                self.vx = 0.0
            if abs(self.z) > bz:
                self.z = math.copysign(bz, self.z)
                self.vz = 0.0

    # ── health ───────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> bool:
        """Subtract *amount* HP.  Returns ``True`` if the entity just died."""
        if not self.is_alive or self.max_health is None:
            return False
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.is_alive = False
            return True
        return False

    def heal(self, amount: int) -> None:
        """Add *amount* HP, capped at ``max_health``."""
        if self.max_health is not None:
            self.health = min(self.max_health, self.health + amount)

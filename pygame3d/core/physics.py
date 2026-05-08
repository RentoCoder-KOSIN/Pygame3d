"""
pygame3d.core.physics
~~~~~~~~~~~~~~~~~~~~~
Simple axis-aligned physics body for character controllers and moving objects.

Not a full rigid-body simulation — designed for arcade/action games that need
predictable, deterministic movement with jump, gravity, and wall collision.
"""
from __future__ import annotations

import math
from typing import Any


class PhysicsBody:
    """Stand-alone physics state that can be composed into any entity.

    Parameters
    ----------
    x, y, z:
        Initial position.
    size:
        Bounding-sphere radius for collision response.
    gravity:
        Downward acceleration per frame.
    jump_power:
        Initial upward velocity on jump.
    base_speed:
        Horizontal movement speed (world-units / frame).
    world_bounds:
        ``(half_x, half_z)`` clamp box.  ``None`` = unbounded.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        *,
        size: float = 0.5,
        gravity: float = -0.02,
        jump_power: float = 0.3,
        base_speed: float = 0.15,
        world_bounds: tuple[float, float] | None = (25.0, 25.0),
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.vx = self.vy = self.vz = 0.0
        self.size = size
        self.gravity = gravity
        self.jump_power = jump_power
        self.base_speed = base_speed
        self.speed = base_speed
        self.world_bounds = world_bounds
        self.on_ground = False
        self.rotation = 0.0

    # ── movement input ────────────────────────────────────────────────────────

    def move(
        self,
        forward: float,
        strafe: float,
        facing_angle: float = 0.0,
        *,
        speed_multiplier: float = 1.0,
    ) -> None:
        """Apply directional movement relative to *facing_angle* (degrees).

        Parameters
        ----------
        forward:
            +1 = move forward, -1 = move backward, 0 = no input.
        strafe:
            +1 = strafe right, -1 = strafe left, 0 = no input.
        facing_angle:
            Camera / character yaw in degrees.
        speed_multiplier:
            Scale applied on top of :attr:`speed`.
        """
        sp = self.speed * speed_multiplier
        if forward or strafe:
            ar = math.radians(facing_angle)
            fx, fz = math.cos(ar), math.sin(ar)
            rx, rz = -math.sin(ar), math.cos(ar)
            self.vx = (fx * forward + rx * strafe) * sp
            self.vz = (fz * forward + rz * strafe) * sp
        else:
            self.vx *= 0.8
            self.vz *= 0.8

    def jump(self) -> bool:
        """Initiate a jump.  Returns ``False`` if already airborne."""
        if not self.on_ground:
            return False
        self.vy = self.jump_power
        self.on_ground = False
        return True

    # ── integration ───────────────────────────────────────────────────────────

    def step(self) -> None:
        """Integrate one frame: apply gravity, integrate velocity, clamp bounds."""
        # gravity
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        # ground
        if self.y <= self.size:
            self.y = self.size
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        # world bounds
        if self.world_bounds:
            bx, bz = self.world_bounds
            if abs(self.x) > bx:
                self.x = math.copysign(bx, self.x)
                self.vx = 0.0
            if abs(self.z) > bz:
                self.z = math.copysign(bz, self.z)
                self.vz = 0.0

    # ── collision helpers ─────────────────────────────────────────────────────

    def overlaps(self, other: "PhysicsBody") -> bool:
        """Sphere–sphere overlap test."""
        d = math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))
        return d < (self.size + other.size)

    def push_back(self, ox: float, oy: float, oz: float) -> None:
        """Restore saved position and kill horizontal velocity (wall response)."""
        self.x, self.y, self.z = ox, oy, oz
        self.vx = self.vz = 0.0

    def get_pos(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def get_forward(self, facing_angle: float) -> tuple[float, float]:
        """Return ``(fx, fz)`` unit vector for the given yaw angle."""
        ar = math.radians(facing_angle)
        return (math.cos(ar), math.sin(ar))

    def __repr__(self) -> str:
        return (
            f"<PhysicsBody pos=({self.x:.2f},{self.y:.2f},{self.z:.2f}) "
            f"vel=({self.vx:.2f},{self.vy:.2f},{self.vz:.2f}) "
            f"on_ground={self.on_ground}>"
        )

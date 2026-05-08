"""Tests for pygame3d.core — no OpenGL / pygame required."""
import math
import sys
import types

# ── stub out OpenGL and pygame so tests run headless ─────────────────────────
for mod in ["OpenGL", "OpenGL.GL", "OpenGL.GLU", "pygame"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

import pytest
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from pygame3d.core.entity    import Entity, DynamicEntity
from pygame3d.core.physics   import PhysicsBody
from pygame3d.core.camera    import Camera
from pygame3d.core.projectile import Projectile
from pygame3d.world.volume   import BoxVolume
from pygame3d.world.road     import Road
from pygame3d.world.procedural import generate_grid_world


# ── Entity ────────────────────────────────────────────────────────────────────

class TestEntity:
    def test_defaults(self):
        e = Entity()
        assert e.x == e.y == e.z == 0.0
        assert e.size == 0.5

    def test_get_set_pos(self):
        e = Entity(1, 2, 3)
        assert e.get_pos() == (1, 2, 3)
        e.set_pos(4, 5, 6)
        assert e.get_pos() == (4, 5, 6)

    def test_distance_to(self):
        a = Entity(0, 0, 0)
        b = Entity(3, 4, 0)
        assert math.isclose(a.distance_to(b), 5.0)

    def test_overlaps(self):
        a = Entity(0, 0, 0, size=1.0)
        b = Entity(1.5, 0, 0, size=1.0)
        assert a.overlaps(b)           # 1.5 < 2.0
        c = Entity(3.0, 0, 0, size=0.5)
        assert not a.overlaps(c)       # 3.0 > 1.5


class TestDynamicEntity:
    def test_take_damage(self):
        e = DynamicEntity(max_health=100)
        died = e.take_damage(40)
        assert not died and e.health == 60

    def test_lethal_damage(self):
        e = DynamicEntity(max_health=50)
        died = e.take_damage(100)
        assert died and e.health == 0 and not e.is_alive

    def test_heal(self):
        e = DynamicEntity(max_health=100)
        e.take_damage(50)
        e.heal(30)
        assert e.health == 80

    def test_heal_cap(self):
        e = DynamicEntity(max_health=100)
        e.heal(9999)
        assert e.health == 100

    def test_indestructible(self):
        e = DynamicEntity(max_health=None)
        died = e.take_damage(99999)
        assert not died

    def test_gravity(self):
        e = DynamicEntity(y=10.0, gravity=-0.02)
        for _ in range(100):
            e.apply_gravity()
        assert e.y == e.size   # settled on ground


# ── PhysicsBody ───────────────────────────────────────────────────────────────

class TestPhysicsBody:
    def test_jump(self):
        pb = PhysicsBody(y=0.5)
        pb.on_ground = True
        ok = pb.jump()
        assert ok
        assert pb.vy > 0

    def test_jump_airborne(self):
        pb = PhysicsBody()
        pb.on_ground = False
        assert not pb.jump()

    def test_world_bounds(self):
        pb = PhysicsBody(world_bounds=(5.0, 5.0))
        pb.vx = 100.0
        for _ in range(20):
            pb.step()
        assert abs(pb.x) <= 5.0

    def test_move_sets_velocity(self):
        pb = PhysicsBody()
        pb.on_ground = True
        pb.move(1, 0, facing_angle=0.0)
        assert pb.vx != 0 or pb.vz != 0


# ── Camera ────────────────────────────────────────────────────────────────────

class TestCamera:
    def test_rotate_clamps_pitch(self):
        cam = Camera()
        cam.rotate(0, 999)
        assert cam.angle_v <= 80.0
        cam.rotate(0, -999)
        assert cam.angle_v >= -80.0

    def test_forward_changes_with_angle(self):
        cam = Camera()
        cam.angle_h = 0.0
        fx0, fz0 = cam.forward
        cam.angle_h = 90.0
        fx1, fz1 = cam.forward
        assert not math.isclose(fx0, fx1)


# ── Projectile ────────────────────────────────────────────────────────────────

class TestProjectile:
    def test_straight_travel(self):
        p = Projectile(0, 1, 0, direction=(1, 0), speed=1.0)
        p.update()
        assert math.isclose(p.x, 1.0)

    def test_direction_normalised(self):
        p = Projectile(0, 0, 0, direction=(3, 4))
        dx, dz = p.direction
        assert math.isclose(math.sqrt(dx*dx + dz*dz), 1.0, rel_tol=1e-6)

    def test_expires_by_lifetime(self):
        p = Projectile(0, 0, 0, direction=(1, 0), lifetime=3)
        for _ in range(3):
            p.update()
        assert not p.is_alive

    def test_collision(self):
        p = Projectile(0, 0, 0, direction=(1, 0), size=0.5)

        class Target:
            x = 0.0; y = 0.0; z = 0.0; size = 0.5

        assert p.check_collision(Target())

    def test_no_collision(self):
        p = Projectile(0, 0, 0, direction=(1, 0), size=0.2)

        class FarTarget:
            x = 10.0; y = 0.0; z = 0.0; size = 0.2

        assert not p.check_collision(FarTarget())

    def test_aoe(self):
        p = Projectile(0, 0, 0, direction=(1, 0), explosion_radius=3.0)

        class Near:
            x = 2.0; y = 0.0; z = 0.0; size = 0.5

        class Far:
            x = 10.0; y = 0.0; z = 0.0; size = 0.5

        hits = p.get_aoe_targets([Near(), Far()])
        assert len(hits) == 1


# ── BoxVolume ─────────────────────────────────────────────────────────────────

class TestBoxVolume:
    def test_collision_inside(self):
        v = BoxVolume(0, 0, 0, width=4, height=4, depth=4)
        assert v.check_collision(0, 2, 0, 0.5)

    def test_no_collision_outside(self):
        v = BoxVolume(0, 0, 0, width=4, height=4, depth=4)
        assert not v.check_collision(10, 2, 0, 0.5)

    def test_check_inside(self):
        v = BoxVolume(0, 0, 0, width=6, height=4, depth=6)
        assert v.check_inside(1, 2, 1)
        assert not v.check_inside(5, 2, 5)


# ── generate_grid_world ───────────────────────────────────────────────────────

class TestGenerateGridWorld:
    def test_returns_lists(self):
        vols, roads = generate_grid_world(map_size=20, seed=0)
        assert isinstance(vols, list)
        assert isinstance(roads, list)

    def test_reproducible(self):
        a, _ = generate_grid_world(map_size=20, seed=42)
        b, _ = generate_grid_world(map_size=20, seed=42)
        assert len(a) == len(b)

    def test_density_zero(self):
        vols, _ = generate_grid_world(map_size=20, density=0.0, seed=1)
        assert vols == []

    def test_density_one(self):
        vols, _ = generate_grid_world(map_size=60, density=1.0, seed=1)
        assert len(vols) > 0

    def test_road_count(self):
        _, roads = generate_grid_world(map_size=20, block_size=8, seed=0)
        assert len(roads) > 0
        assert all(isinstance(r, Road) for r in roads)

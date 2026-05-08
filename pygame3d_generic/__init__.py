"""
pygame3d
~~~~~~~~
Generic Pygame + OpenGL 3-D game engine library.

Provides reusable building blocks for any 3-D game:

- **Core** — entity base classes, camera, physics body, projectile
- **Render** — OpenGL primitives, ground/grid, HUD, overlay, particle system
- **World** — collision volumes, roads, procedural grid layouts
- **Network** — TCP server & client with callback-based message API

Quick-start
-----------
>>> import pygame3d
>>> print(pygame3d.__version__)
'0.3.0'

>>> from pygame3d.core import Entity, DynamicEntity, Camera, PhysicsBody
>>> from pygame3d.world import BoxVolume, Road, generate_grid_world
>>> from pygame3d.network import NetworkServer, NetworkClient
"""

from .core.entity    import Entity, DynamicEntity
from .core.camera    import Camera
from .core.physics   import PhysicsBody
from .core.projectile import Projectile

from .render.primitives import draw_cube, draw_sphere, draw_cylinder, draw_character_capsule
from .render.scene      import draw_ground, draw_grid, setup_lighting
from .render.hud        import HUD
from .render.overlay    import TextOverlay
from .render.particles  import Particle, ParticleSystem

from .world.volume    import Volume, BoxVolume
from .world.road      import Road
from .world.procedural import generate_grid_world

from .network.server import NetworkServer
from .network.client import NetworkClient

__version__ = "0.3.0"

__all__ = [
    # core
    "Entity", "DynamicEntity",
    "Camera",
    "PhysicsBody",
    "Projectile",
    # render
    "draw_cube", "draw_sphere", "draw_cylinder", "draw_character_capsule",
    "draw_ground", "draw_grid", "setup_lighting",
    "HUD", "TextOverlay",
    "Particle", "ParticleSystem",
    # world
    "Volume", "BoxVolume",
    "Road",
    "generate_grid_world",
    # network
    "NetworkServer", "NetworkClient",
]

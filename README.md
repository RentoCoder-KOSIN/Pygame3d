# pygame3d

[![PyPI](https://img.shields.io/pypi/v/pygame3d-generic)](https://pypi.org/project/pygame3d-generic/)
[![Python](https://img.shields.io/pypi/pyversions/pygame3d-generic)](https://pypi.org/project/pygame3d-generic/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**pygame3d** は Pygame + PyOpenGL 製の汎用 3D ゲームエンジンライブラリです。  
FPS・TPS・アドベンチャー・シミュレーターなど、あらゆるジャンルの 3D ゲームに使える  
汎用コンポーネントをひとつのパッケージに収めています。

---

## インストール

```bash
pip install pygame3d-generic
```

GPU アクセラレータ付き（任意）:

```bash
pip install "pygame3d-generic[accelerate]"
```

開発用:

```bash
pip install "pygame3d-generic[dev]"
```

---

## パッケージ構成

```
pygame3d-generic/
├── core/        # Entity, DynamicEntity, Camera, PhysicsBody, Projectile
├── render/      # OpenGL プリミティブ・グリッド・HUD・オーバーレイ・パーティクル
├── world/       # BoxVolume, Road, generate_grid_world
└── network/     # NetworkServer, NetworkClient
```

---

## クイックスタート

### エンティティ & 物理

```python
from pygame3d-generic.core import DynamicEntity, PhysicsBody, Camera

# 物理ボディを持つキャラクター
body = PhysicsBody(x=0, y=1, z=0, base_speed=0.15, gravity=-0.02)

# キー入力で移動（facing_angle はカメラ水平角度）
body.move(forward=1, strafe=0, facing_angle=camera.angle_h)
body.jump()   # 接地中のみ有効

# フレームごとに呼ぶ
body.step()

# カメラ
camera = Camera(fov=60.0, distance=10.0)
camera.rotate(mouse_dx, mouse_dy)
camera.follow(body.x, body.y, body.z)  # サードパーソン追従
```

### プロジェクタイル（汎用飛翔体）

```python
from pygame3d-generic.core import Projectile

# 直線弾
bullet = Projectile(
    x=0, y=1, z=0,
    direction=(1, 0),    # (dx, dz) 正規化不要
    speed=0.8,
    damage=25,
    size=0.15,
    color=[1.0, 0.8, 0.2],
)

# ホーミング弾（最近傍ターゲットを追尾）
homing = Projectile(
    x=0, y=1, z=0,
    direction=(0, 1),
    speed=0.5,
    damage=40,
    is_homing=True,
)

# フレームごとに更新
alive = bullet.update()
alive = homing.update(targets=[enemy_a, enemy_b])

# 衝突判定
if bullet.check_collision(enemy):
    enemy.take_damage(bullet.damage)

# 範囲攻撃（爆発半径内の全ターゲットを返す）
splash_bullet = Projectile(..., explosion_radius=3.0)
hit_list = splash_bullet.get_aoe_targets(enemies)
```

### DynamicEntity でカスタムキャラクター

```python
from pygame3d-generic.core import DynamicEntity

class Player(DynamicEntity):
    def __init__(self):
        super().__init__(max_health=100, speed=0.15)
        self.score = 0

class Enemy(DynamicEntity):
    def __init__(self, x, z):
        super().__init__(x=x, z=z, max_health=50,
                         color=[0.9, 0.1, 0.1])

player = Player()
enemy  = Enemy(5, 5)

# ダメージ
died = enemy.take_damage(30)   # True なら enemy.is_alive == False
player.heal(20)

# 距離・衝突
dist = player.distance_to(enemy)
if player.overlaps(enemy):
    player.take_damage(10)
```

### ワールド生成

```python
from pygame3d-generic.world import generate_grid_world, BoxVolume, Road

# プロシージャル都市（seed 固定で再現可能）
volumes, roads = generate_grid_world(
    map_size=40,
    block_size=8,
    density=0.7,
    seed=42,
    height_range=(3.0, 20.0),
)

# 独自ボリューム（建物・壁・プラットフォーム等）
wall     = BoxVolume(10, 0, 0, width=0.5, height=5, depth=10)
platform = BoxVolume(5, 2, 5, width=6, height=0.5, depth=6,
                     color=[0.3, 0.6, 0.3])
door_box = BoxVolume(0, 0, 0, width=4, height=4, depth=4,
                     entrance_side="front", entrance_width=0.4)

# コリジョン
if wall.check_collision(px, py, pz, radius=0.5):
    ...
```

### レンダリング

```python
from pygame3d-generic.render import (
    setup_lighting,
    draw_ground, draw_grid,
    draw_sphere, draw_cube, draw_cylinder, draw_character_capsule,
    HUD, TextOverlay,
    ParticleSystem,
)

# ライティング初期化（OpenGL コンテキスト作成後に 1 回）
setup_lighting()

# 各フレームのレンダリング
draw_ground(half_size=40)
draw_grid(half_size=20, step=2.0)

# プリミティブ（カレント行列位置に描画）
draw_sphere(radius=0.5, color=[0.2, 0.8, 0.3])
draw_cube(half_size=1.0, color=[0.6, 0.6, 0.7])
draw_cylinder(radius=0.4, height=2.0, color=[0.8, 0.5, 0.2])
draw_character_capsule(height=1.8, radius=0.5, color=[0.2, 0.6, 0.9])

# HUD（テキスト・バー）
hud = HUD(display=(800, 600))
hud.begin_2d()
hud.draw_text("HP: 80/100", x=10, y=10, color=(255, 255, 255))
hud.draw_bar(10, 50, 200, 20, value=0.8, fg_color=(50, 220, 50))
hud.draw_panel(0, 0, 300, 120, color=(0, 0, 0, 120))
hud.end_2d()

# フルスクリーンオーバーレイ（ポーズ・ゲームオーバー等）
overlay = TextOverlay(display=(800, 600))
overlay.draw_message("PAUSED", subtitle="Press P to resume")

# パーティクル
ps = ParticleSystem(max_particles=500)
ps.emit(x=0, y=1, z=0, count=30, color=[1.0, 0.4, 0.0])
ps.update()
ps.draw()
```

### ネットワーク

```python
from pygame3d-generic.network import NetworkServer, NetworkClient

# ── サーバー ──────────────────────────────────────────────────────────
server = NetworkServer(port=8888, tick_rate=30)

@server.on("move")
def on_move(player_id, msg):
    server.player_data[player_id].update(
        x=msg["x"], y=msg["y"], z=msg["z"]
    )

@server.on("chat")
def on_chat(player_id, msg):
    server.broadcast({"type": "chat", "from": player_id, "text": msg["text"]})

@server.on("disconnect")
def on_leave(player_id, _msg):
    print(f"Player {player_id} left")

server.start()

# ── クライアント ──────────────────────────────────────────────────────
client = NetworkClient("localhost", 8888)

@client.on("state_update")
def on_state(msg):
    render_world(msg["game_state"])

@client.on("chat")
def on_chat(msg):
    print(f"[{msg['from']}] {msg['text']}")

client.connect()

# ゲームループ内
client.send_position(player.x, player.y, player.z)
client.send({"type": "chat", "text": "Hello!"})
```

---

## 依存パッケージ

| パッケージ | バージョン |
|-----------|-----------|
| pygame    | >= 2.5    |
| PyOpenGL  | >= 3.1    |

---

## PyPI へのアップロード

```bash
# ビルド
python -m build

# テスト PyPI（初回確認推奨）
twine upload --repository testpypi dist/*

# 本番 PyPI
twine upload dist/*
```

---

## ライセンス

MIT

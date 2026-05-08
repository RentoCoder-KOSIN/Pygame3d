"""
pygame3d.network.server
~~~~~~~~~~~~~~~~~~~~~~~
Generic multi-client TCP game server with a callback-based message API.

The server has *no* built-in game logic (no coins, no enemies, no lives).
All message handling is done via the :meth:`on` decorator — callers register
handlers for whatever message types their game uses.

Usage
-----
>>> from pygame3d.network import NetworkServer
>>> server = NetworkServer(port=8888)
>>>
>>> @server.on("move")
... def handle_move(player_id, msg):
...     print(f"Player {player_id} moved to", msg["x"], msg["z"])
...     server.broadcast({"type": "state", "players": server.player_data})
>>>
>>> server.start()
"""
from __future__ import annotations

import json
import socket
import threading
import time
from typing import Callable, Any


class NetworkServer:
    """TCP server that broadcasts state to all clients.

    Parameters
    ----------
    host:
        Bind address.  ``"0.0.0.0"`` accepts from all interfaces.
    port:
        TCP port to listen on.
    tick_rate:
        Automatic state-broadcast frequency in Hz.
        Set to ``0`` to disable automatic broadcasts.
    """

    _DEFAULT_COLORS: list[list[float]] = [
        [0.2, 0.8, 0.3], [0.2, 0.3, 0.8], [0.8, 0.2, 0.6],
        [0.8, 0.6, 0.2], [0.8, 0.2, 0.2], [0.2, 0.8, 0.8],
    ]

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8888,
        tick_rate: float = 30.0,
    ) -> None:
        self.host      = host
        self.port      = port
        self.tick_rate = tick_rate

        self._socket:  socket.socket | None = None
        self._clients: list[tuple]          = []   # (sock, addr, pid)
        self._handlers: dict[str, list[Callable]] = {}
        self._next_pid  = 1
        self._lock      = threading.Lock()
        self.running    = False

        # caller-mutable game state; broadcast each tick
        self.game_state: dict[str, Any] = {}
        # per-player data: {pid: {"x": 0, "y": 1, "z": 0, "color": [...]}}
        self.player_data: dict[int, dict] = {}

    # ── decorator API ─────────────────────────────────────────────────────────

    def on(self, message_type: str) -> Callable:
        """Register a handler for *message_type*.

        The handler is called as ``fn(player_id: int, msg: dict)``.

        >>> @server.on("chat")
        ... def on_chat(pid, msg):
        ...     server.broadcast({"type": "chat", "from": pid, "text": msg["text"]})
        """
        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(message_type, []).append(fn)
            return fn
        return decorator

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start accepting connections (non-blocking, uses daemon threads)."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(10)
        self.running = True
        print(f"[pygame3d] Server listening on {self.host}:{self.port}")
        threading.Thread(target=self._accept_loop, daemon=True).start()
        if self.tick_rate > 0:
            threading.Thread(target=self._broadcast_loop, daemon=True).start()

    def stop(self) -> None:
        """Shut down the server."""
        self.running = False
        if self._socket:
            self._socket.close()

    # ── send / broadcast ──────────────────────────────────────────────────────

    def broadcast(self, data: dict) -> None:
        """Send *data* to every connected client."""
        payload = (json.dumps(data) + "\n").encode()
        dead: list[int] = []
        for i, (cs, _, _pid) in enumerate(self._clients):
            try:
                cs.sendall(payload)
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            _, _, pid = self._clients.pop(i)
            self._on_disconnect(pid)

    def send_to(self, player_id: int, data: dict) -> bool:
        """Send *data* to a specific player.  Returns False if not found."""
        payload = (json.dumps(data) + "\n").encode()
        with self._lock:
            for cs, _, pid in self._clients:
                if pid == player_id:
                    try:
                        cs.sendall(payload)
                        return True
                    except Exception:
                        return False
        return False

    # ── internal ──────────────────────────────────────────────────────────────

    def _accept_loop(self) -> None:
        while self.running:
            try:
                cs, addr = self._socket.accept()
                cs.settimeout(5.0)
                with self._lock:
                    pid = self._next_pid
                    self._next_pid += 1
                    self._clients.append((cs, addr, pid))
                    self.player_data[pid] = {
                        "x": 0.0, "y": 1.0, "z": 0.0,
                        "color": self._DEFAULT_COLORS[pid % len(self._DEFAULT_COLORS)],
                    }
                print(f"[pygame3d] Client connected: {addr} (id={pid})")
                self._send(cs, {
                    "type": "init",
                    "player_id": pid,
                    "game_state": self.game_state,
                })
                threading.Thread(target=self._client_loop, args=(cs, pid), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"[pygame3d] Accept error: {e}")

    def _client_loop(self, cs: socket.socket, pid: int) -> None:
        buf = b""
        while self.running:
            try:
                data = cs.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line:
                        try:
                            self._dispatch(pid, json.loads(line.decode()))
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except Exception:
                break
        self._on_disconnect(pid)

    def _dispatch(self, pid: int, msg: dict) -> None:
        t = msg.get("type")
        # built-in: position sync
        if t == "position":
            with self._lock:
                if pid in self.player_data:
                    for k in ("x", "y", "z"):
                        if k in msg:
                            self.player_data[pid][k] = msg[k]
        # user handlers
        for fn in self._handlers.get(t, []):
            try:
                fn(pid, msg)
            except Exception as exc:
                print(f"[pygame3d] Handler error '{t}': {exc}")

    def _broadcast_loop(self) -> None:
        interval = 1.0 / self.tick_rate
        while self.running:
            time.sleep(interval)
            with self._lock:
                gs = dict(self.game_state)
                gs["players"] = dict(self.player_data)
            self.broadcast({"type": "state_update", "game_state": gs})

    def _send(self, cs: socket.socket, data: dict) -> None:
        try:
            cs.sendall((json.dumps(data) + "\n").encode())
        except Exception as e:
            print(f"[pygame3d] Send error: {e}")

    def _on_disconnect(self, pid: int) -> None:
        with self._lock:
            self.player_data.pop(pid, None)
            self._clients = [(s, a, p) for s, a, p in self._clients if p != pid]
        # call user handlers
        for fn in self._handlers.get("disconnect", []):
            try:
                fn(pid, {})
            except Exception:
                pass
        print(f"[pygame3d] Player {pid} disconnected")

    @property
    def player_count(self) -> int:
        return len(self._clients)

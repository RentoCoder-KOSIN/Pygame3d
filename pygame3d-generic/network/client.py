"""
pygame3d.network.client
~~~~~~~~~~~~~~~~~~~~~~~
Generic TCP game client with a decorator-based message API.

The client has *no* built-in game logic.  All behaviour is registered via
:meth:`on`.  The only built-in behaviour is storing ``player_id`` and
``game_state`` from the server's ``init`` message.

Usage
-----
>>> from pygame3d.network import NetworkClient
>>> client = NetworkClient("localhost", 8888)
>>>
>>> @client.on("state_update")
... def on_state(msg):
...     render(msg["game_state"])
>>>
>>> client.connect()
>>> client.send({"type": "position", "x": 1.0, "y": 1.0, "z": 2.0})
"""
from __future__ import annotations

import json
import socket
import threading
from typing import Callable, Any


class NetworkClient:
    """TCP client that syncs with a :class:`~pygame3d.network.server.NetworkServer`.

    Parameters
    ----------
    host:
        Server hostname or IP.
    port:
        Server port.
    """

    def __init__(self, host: str = "localhost", port: int = 8888) -> None:
        self.host  = host
        self.port  = port
        self._socket: socket.socket | None = None
        self.connected  = False
        self.running    = False
        self.player_id: int | None = None
        self.game_state: dict[str, Any] = {}
        self._handlers: dict[str, list[Callable]] = {}

    # ── decorator API ─────────────────────────────────────────────────────────

    def on(self, message_type: str) -> Callable:
        """Register a handler for *message_type*.

        The handler is called as ``fn(msg: dict)``.

        >>> @client.on("chat")
        ... def on_chat(msg):
        ...     print(f"[{msg['from']}] {msg['text']}")
        """
        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(message_type, []).append(fn)
            return fn
        return decorator

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to the server.  Returns ``True`` on success."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.port))
            self._socket.settimeout(5.0)
            self.connected = self.running = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            print(f"[pygame3d] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[pygame3d] Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Close the connection."""
        self.running = self.connected = False
        if self._socket:
            self._socket.close()

    # ── send ─────────────────────────────────────────────────────────────────

    def send(self, data: dict) -> None:
        """Send an arbitrary message dict to the server."""
        if not self.connected or not self._socket:
            return
        try:
            self._socket.sendall((json.dumps(data) + "\n").encode())
        except Exception as e:
            print(f"[pygame3d] Send error: {e}")
            self.connected = False

    def send_position(self, x: float, y: float, z: float) -> None:
        """Convenience: send the local player's position."""
        self.send({"type": "position", "x": x, "y": y, "z": z})

    # ── internal ─────────────────────────────────────────────────────────────

    def _recv_loop(self) -> None:
        buf = b""
        while self.running and self.connected:
            try:
                data = self._socket.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line:
                        try:
                            self._dispatch(json.loads(line.decode()))
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except Exception:
                break
        self.connected = False
        print("[pygame3d] Disconnected from server")

    def _dispatch(self, msg: dict) -> None:
        t = msg.get("type")
        # built-ins
        if t == "init":
            self.player_id  = msg.get("player_id")
            self.game_state = msg.get("game_state", {})
        elif t == "state_update":
            self.game_state = msg.get("game_state", {})
        # user handlers
        for fn in self._handlers.get(t, []):
            try:
                fn(msg)
            except Exception as exc:
                print(f"[pygame3d] Handler error '{t}': {exc}")

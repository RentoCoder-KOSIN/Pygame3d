"""
pygame3d.render.hud
~~~~~~~~~~~~~~~~~~~
Generic HUD renderer: draw arbitrary text and bar graphs over an OpenGL scene.

Usage
-----
>>> hud = HUD(display=(800, 600))
>>> # inside your render loop:
>>> hud.begin_2d()
>>> hud.draw_text("Score: 1200", 10, 10)
>>> hud.draw_bar(10, 50, 200, 20, value=0.75, color=(0, 220, 0))
>>> hud.end_2d()
"""
from __future__ import annotations

from typing import Sequence

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYGAME_AVAILABLE = False

try:
    from OpenGL.GL import (
        glDisable, glEnable, glBegin, glEnd,
        glTexCoord2f, glVertex2f, glColor4f,
        glMatrixMode, glPushMatrix, glPopMatrix, glLoadIdentity, glOrtho,
        glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, glDeleteTextures,
        glBlendFunc,
        GL_DEPTH_TEST, GL_LIGHTING, GL_BLEND, GL_QUADS,
        GL_TEXTURE_2D, GL_LINEAR, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER,
        GL_RGBA, GL_UNSIGNED_BYTE,
        GL_PROJECTION, GL_MODELVIEW,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    )
    _OPENGL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENGL_AVAILABLE = False


class HUD:
    """Overlay 2-D text and bars onto an OpenGL window via pygame fonts.

    Parameters
    ----------
    display:
        ``(width, height)`` of the window in pixels.
    font_size:
        Default pygame font size.
    """

    def __init__(self, display: tuple[int, int], font_size: int = 36) -> None:
        if not _PYGAME_AVAILABLE:
            raise RuntimeError("pygame is required for HUD.  Run: pip install pygame")
        if not _OPENGL_AVAILABLE:
            raise RuntimeError("PyOpenGL is required for HUD.")
        self.display = display
        self._font = pygame.font.Font(None, font_size)
        self._surface: pygame.Surface | None = None

    # ── 2-D mode ─────────────────────────────────────────────────────────────

    def begin_2d(self) -> None:
        """Switch to orthographic projection for HUD rendering."""
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def end_2d(self) -> None:
        """Restore perspective projection."""
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    # ── drawing primitives ────────────────────────────────────────────────────

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (255, 255, 255),
        font_size: int | None = None,
    ) -> None:
        """Blit antialiased text at screen position ``(x, y)``.

        Parameters
        ----------
        text:
            String to render.
        x, y:
            Top-left pixel position.
        color:
            ``(r, g, b)`` 0–255.
        font_size:
            Override the default font size for this call.
        """
        font = pygame.font.Font(None, font_size) if font_size else self._font
        surf = font.render(text, True, color)
        self._blit_surface(surf, x, y)

    def draw_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        value: float,
        *,
        fg_color: tuple[int, int, int] = (50, 220, 50),
        bg_color: tuple[int, int, int] = (60, 60, 60),
        border_color: tuple[int, int, int] | None = (200, 200, 200),
    ) -> None:
        """Draw a filled progress bar.

        Parameters
        ----------
        x, y:
            Top-left corner in screen pixels.
        width, height:
            Bar dimensions in pixels.
        value:
            Fill fraction 0.0–1.0.
        fg_color:
            Filled portion colour.
        bg_color:
            Empty portion colour.
        border_color:
            1-px border colour.  ``None`` disables the border.
        """
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill(bg_color)
        fill_w = max(0, int(width * min(1.0, max(0.0, value))))
        if fill_w > 0:
            surf.fill(fg_color, (0, 0, fill_w, height))
        if border_color:
            pygame.draw.rect(surf, border_color, (0, 0, width, height), 1)
        self._blit_surface(surf, x, y)

    def draw_panel(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int, int] = (0, 0, 0, 140),
    ) -> None:
        """Draw a semi-transparent panel background.

        Parameters
        ----------
        x, y:
            Top-left corner.
        width, height:
            Panel dimensions.
        color:
            ``(r, g, b, a)`` — alpha is 0–255.
        """
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill(color)
        self._blit_surface(surf, x, y)

    # ── internal ──────────────────────────────────────────────────────────────

    def _blit_surface(self, surface: "pygame.Surface", x: int, y: int) -> None:
        w, h = surface.get_size()
        data = pygame.image.tostring(surface, "RGBA", True)
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        from OpenGL.GL import glEnable as _en, glDisable as _dis
        _en(GL_TEXTURE_2D)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x,     y)
        glTexCoord2f(1, 1); glVertex2f(x + w, y)
        glTexCoord2f(1, 0); glVertex2f(x + w, y + h)
        glTexCoord2f(0, 0); glVertex2f(x,     y + h)
        glEnd()
        _dis(GL_TEXTURE_2D)
        glDeleteTextures([tid])

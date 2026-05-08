"""
pygame3d.render.overlay
~~~~~~~~~~~~~~~~~~~~~~~
Full-screen text overlay for menus, pause screens, notifications, etc.

Usage
-----
>>> overlay = TextOverlay(display=(800, 600))
>>> overlay.draw_message("PAUSED", subtitle="Press P to resume")
"""
from __future__ import annotations

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
        GL_RGBA, GL_UNSIGNED_BYTE, GL_PROJECTION, GL_MODELVIEW,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    )
    _OPENGL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENGL_AVAILABLE = False


class TextOverlay:
    """Render a full-screen semi-transparent overlay with centred text.

    Parameters
    ----------
    display:
        ``(width, height)`` window size in pixels.
    title_size:
        Font size for the main title.
    subtitle_size:
        Font size for subtitle / instruction lines.
    """

    def __init__(
        self,
        display: tuple[int, int],
        title_size: int = 72,
        subtitle_size: int = 36,
    ) -> None:
        if not (_PYGAME_AVAILABLE and _OPENGL_AVAILABLE):
            raise RuntimeError("pygame and PyOpenGL are required for TextOverlay.")
        self.display = display
        self._font_title = pygame.font.Font(None, title_size)
        self._font_sub   = pygame.font.Font(None, subtitle_size)

    def draw_message(
        self,
        title: str,
        subtitle: str | None = None,
        *,
        title_color: tuple[int, int, int] = (255, 255, 255),
        subtitle_color: tuple[int, int, int] = (200, 200, 200),
        bg_alpha: int = 140,
    ) -> None:
        """Draw an overlay with a large *title* and optional *subtitle*.

        Parameters
        ----------
        title:
            Main heading text.
        subtitle:
            Secondary / instruction text rendered below the title.
        title_color:
            RGB colour for the title.
        subtitle_color:
            RGB colour for the subtitle.
        bg_alpha:
            Opacity of the dark background panel (0–255).
        """
        W, H = self.display
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, bg_alpha))

        title_surf = self._font_title.render(title, True, title_color)
        tx = (W - title_surf.get_width()) // 2
        ty = H // 2 - title_surf.get_height()
        surf.blit(title_surf, (tx, ty))

        if subtitle:
            sub_surf = self._font_sub.render(subtitle, True, subtitle_color)
            sx = (W - sub_surf.get_width()) // 2
            sy = H // 2 + 10
            surf.blit(sub_surf, (sx, sy))

        self._draw_surface(surf)

    # ── internal ──────────────────────────────────────────────────────────────

    def _draw_surface(self, surf: "pygame.Surface") -> None:
        w, h = surf.get_size()
        data = pygame.image.tostring(surf, "RGBA", True)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix(); glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix(); glLoadIdentity()

        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glEnable(GL_TEXTURE_2D)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(w, 0)
        glTexCoord2f(1, 0); glVertex2f(w, h)
        glTexCoord2f(0, 0); glVertex2f(0, h)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([tid])

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

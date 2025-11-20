# theme.py

import pygame
from pathlib import Path
from typing import NamedTuple, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Color Schemes
# ─────────────────────────────────────────────────────────────────────────────

class ColorScheme(NamedTuple):
    bg: tuple[int, int, int]
    bg_alt: tuple[int, int, int]
    fg: tuple[int, int, int]
    fg_dim: tuple[int, int, int]
    border_light: tuple[int, int, int]
    border_dark: tuple[int, int, int]
    border_active: tuple[int, int, int]
    accent: tuple[int, int, int]
    accent_hover: tuple[int, int, int]
    error: tuple[int, int, int]


# Predefined schemes
class Schemes:
    EIGHT_BIT = ColorScheme(
        bg=(32, 32, 48),
        bg_alt=(48, 48, 64),
        fg=(240, 240, 240),
        fg_dim=(160, 160, 180),
        border_light=(160, 160, 180),
        border_dark=(64, 64, 96),
        border_active=(255, 220, 100),
        accent=(80, 200, 255),
        accent_hover=(120, 220, 255),
        error=(255, 80, 80),
    )

    DARK = ColorScheme(
        bg=(24, 24, 24),
        bg_alt=(32, 32, 32),
        fg=(220, 220, 220),
        fg_dim=(120, 120, 120),
        border_light=(80, 80, 80),
        border_dark=(16, 16, 16),
        border_active=(100, 180, 255),
        accent=(60, 140, 220),
        accent_hover=(80, 160, 240),
        error=(220, 60, 60),
    )

    LIGHT = ColorScheme(
        bg=(248, 248, 248),
        bg_alt=(238, 238, 238),
        fg=(24, 24, 24),
        fg_dim=(120, 120, 120),
        border_light=(220, 220, 220),
        border_dark=(180, 180, 180),
        border_active=(60, 140, 220),
        accent=(50, 120, 200),
        accent_hover=(70, 140, 220),
        error=(200, 50, 50),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Theme Object (no pygame init side-effects)
# ─────────────────────────────────────────────────────────────────────────────

class Theme:
    def __init__(
        self,
        name: str = "8bit",
        colors: ColorScheme = Schemes.EIGHT_BIT,
        font_path: Optional[str] = None,
        font_size: int = 10,
        padding: int = 4,
        radius: int = 0,
        border_width: int = 2,
    ):
        self.name = name
        self.colors = colors
        self.padding = padding
        self.radius = radius
        self.border_width = border_width

        self._font_path = font_path
        self._font_size = font_size
        self._font: Optional[pygame.font.Font] = None

    # ────────────────────────────────────────────────────────────────────
    # Lazy font loader
    # ────────────────────────────────────────────────────────────────────

    @property
    def get_font(self) -> pygame.font.Font:
        if self._font is not None:
            return self._font

        self._font = self._load_font(self._font_path, self._font_size)
        return self._font

    def _load_font(self, font_path: Optional[str], size: int) -> pygame.font.Font:
        """
        Load font with a proper fallback chain.
        Does NOT call pygame.init().
        """

        search_paths = []

        # 1. explicit user path
        if font_path:
            search_paths.append(Path(font_path))

        # 2. bundled assets directory
        bundled = [Path(__file__).parent / "assets" / "Chicago-12.ttf"]
        search_paths.extend(bundled)

        # Try search paths
        for path in search_paths:
            try:
                if path.exists():
                    return pygame.font.Font(str(path), size)
            except Exception:
                pass

        # 3. system fallback (monospace)
        try:
            return pygame.font.SysFont("Consolas", size)
        except Exception:
            pass

        # 4. last-resort pygame built-in font
        return pygame.font.Font(None, size)

    # ────────────────────────────────────────────────────────────────────

    def render_text(self, text: str, color: tuple[int, int, int], antialias: bool = False):
        return self.font.render(text, antialias, color)

    def __repr__(self):
        return f"<Theme '{self.name}'>"


# ─────────────────────────────────────────────────────────────────────────────
# Global theme management (default = 8bit)
# ─────────────────────────────────────────────────────────────────────────────

_active_theme: Optional[Theme] = None


def set_theme(theme: Theme) -> None:
    global _active_theme
    _active_theme = theme


def get_theme() -> Theme:
    """
    Always returns a working theme.
    If none was set, returns the default 8bit theme.
    """
    global _active_theme

    if _active_theme is None:
        _active_theme = Theme(name="8bit", colors=Schemes.EIGHT_BIT, font_size=10)

    return _active_theme

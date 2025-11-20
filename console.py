# console.py

import pygame
import time
from typing import List, Optional
from component import Component
from theme import get_theme

class Console(Component):
    def __init__(self, x: int = 0, y: int = 0, w: int = 600, h: int = 200, *,
                 max_lines: int = 200,
                 font: Optional[pygame.font.Font] = None):
        super().__init__(x, y, w, h)
        self.theme = get_theme()
        self.max_lines = max_lines
        self.bg_color = self.theme.colors.bg_alt
        self.text_color = self.theme.colors.accent
        self.timestamp_color = self.theme.colors.error
        self.theme = get_theme()
        self.font = self.theme.get_font

        self._lines: List[str] = []
        self._timestamps: List[float] = []
        self._surface_cache: Optional[pygame.Surface] = None
        self._dirty = True

    def log(self, message: str, level: str = "INFO") -> None:
        """Append a log line. Thread-unsafe — call from main thread only."""
        now = time.time()
        prefix = f"[{level[:4]}] {time.strftime('%H:%M:%S', time.localtime(now))}.{int((now % 1)*1000):03d}"
        line = f"{prefix} {message}"
        self._lines.append(line)
        self._timestamps.append(now)
        if len(self._lines) > self.max_lines:
            self._lines.pop(0)
            self._timestamps.pop(0)
        self._dirty = True

    def clear(self) -> None:
        self._lines.clear()
        self._timestamps.clear()
        self._dirty = True

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        # Lazy render to internal surface
        if self._dirty:
            self._render_cache()

        if self._surface_cache:
            surface.blit(self._surface_cache, (self.rect.x, self.rect.y))

        # Draw border
        pygame.draw.rect(surface, (50, 50, 70), self.rect, 1)

    def _render_cache(self) -> None:
        self._surface_cache = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self._surface_cache.fill(self.bg_color)

        line_height = self.font.get_linesize()
        visible_lines = self.rect.h // line_height
        start_idx = max(0, len(self._lines) - visible_lines)

        y = 0
        for i in range(start_idx, len(self._lines)):
            if y >= self.rect.h:
                break
            text = self._lines[i]
            try:
                # Split timestamp and message for coloring
                ts_end = text.find("]")
                if ts_end != -1:
                    ts_part = text[:ts_end+1]
                    msg_part = text[ts_end+1:]
                    ts_surf = self.font.render(ts_part, True, self.timestamp_color)
                    msg_surf = self.font.render(msg_part, True, self.text_color)
                    if ts_surf.get_width() + msg_surf.get_width() <= self.rect.w:
                        self._surface_cache.blit(ts_surf, (2, y))
                        self._surface_cache.blit(msg_surf, (2 + ts_surf.get_width(), y))
                    else:
                        # Fallback: single-color if overflow
                        full_surf = self.font.render(text, True, self.text_color)
                        self._surface_cache.blit(full_surf, (2, y))
                else:
                    full_surf = self.font.render(text, True, self.text_color)
                    self._surface_cache.blit(full_surf, (2, y))
            except Exception:
                # Defensive: skip broken lines
                pass
            y += line_height

        self._dirty = False
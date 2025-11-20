import pygame
from component import Component
from theme import get_theme

# Tier 1 Components
# - Label
# - Image

class Label(Component):
    def __init__(self, x=0, y=0, w=0, h=0, *, caption: str):
        super().__init__(x, y, w, h)
        self.text = caption
        self.theme = get_theme()
        self.font = self.theme.get_font
        self.color = self.theme.colors.accent
        self._surface_cache = None
        self._dirty = True

    def set_text(self, text: str):
        if text != self.text:
            self.text = text
            self._dirty = True

    def _render_cache(self):
        txt = self.font.render(self.text, True, self.color)
        if self.rect.w == 0: self.rect.w = txt.get_width()
        if self.rect.h == 0: self.rect.h = txt.get_height()
        self._surface_cache = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self._surface_cache.blit(txt, (0, 0))
        self._dirty = False

    def draw(self, surface: pygame.Surface):
        if not self.visible: return
        if self._dirty: self._render_cache()
        surface.blit(self._surface_cache, (self.rect.x, self.rect.y))

class Image(Component):
    def __init__(self, x=0, y=0, w=0, h=0, *, img: pygame.Surface):
        super().__init__(x, y, w, h)
        self.img = img
        if self.rect.w == 0 or self.rect.h == 0:
            self.rect.w, self.rect.h = img.get_size()

    def draw(self, surface: pygame.Surface):
        if not self.visible: return
        surface.blit(self.img, (self.rect.x, self.rect.y))
        
        
class Button(Component):
    def __init__(self, text, x=0, y=0, w=120, h=32, *, on_click=None):
        super().__init__(x, y, w, h)
        self.text = text
        self.on_click = on_click
        self.theme = get_theme()
        self.font = self.theme.get_font
        self.text_color = self.theme.colors.fg

        self.bg_normal = self.theme.colors.accent
        self.bg_hover = self.theme.colors.accent_hover
        self.bg_pressed = self.theme.colors.accent_hover

        self.state = "normal"
        self._surface_cache = None
        self._dirty = True

    def _render_cache(self):
        surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        # Background
        bg = {
            "normal": self.bg_normal,
            "hover": self.bg_hover,
            "pressed": self.bg_pressed
        }[self.state]
        surf.fill(bg)

        # Text centered
        txt = self.font.render(self.text, True, self.text_color)
        t_rect = txt.get_rect(center=(self.rect.w // 2, self.rect.h // 2))
        surf.blit(txt, t_rect)

        # Optional border
        pygame.draw.rect(surf, (25, 25, 40), (0, 0, self.rect.w, self.rect.h), 1)

        self._surface_cache = surf
        self._dirty = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if self.state != "pressed":
                    self.state = "hover"
                    self._dirty = True
            else:
                if self.state != "pressed":
                    self.state = "normal"
                    self._dirty = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = "pressed"
                self._dirty = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state == "pressed":
                inside = self.rect.collidepoint(event.pos)
                self.state = "hover" if inside else "normal"
                self._dirty = True
                if inside and self.on_click:
                    self.on_click(self)

    def draw(self, surface):
        if not self.visible: return
        if self._dirty: self._render_cache()
        surface.blit(self._surface_cache, (self.rect.x, self.rect.y))

class Overlay(Component):
    def __init__(self, x=0, y=0, w=400, h=300, *, cell_size=20):
        super().__init__(x, y, w, h)
        self.theme = get_theme()
        self.base_cell_size = cell_size
        self.grid_color = self.theme.colors.border_dark
        self.major_tick_color = self.theme.colors.border_light
        self.adaptive_size = cell_size
        
    def _calculate_adaptive_size(self):
        # Adjust cell size to fit grid nicely within current dimensions
        width_units = max(10, self.rect.w // self.base_cell_size)
        height_units = max(10, self.rect.h // self.base_cell_size)
        
        # Find cell size that gives clean division
        self.adaptive_size = min(
            self.rect.w // width_units,
            self.rect.h // height_units
        )
        self.adaptive_size = max(8, self.adaptive_size)  # Minimum size
        
    def update(self, dt):
        if self.parent:
            new_w = self.parent.rect.w
            new_h = self.parent.rect.h - 25
            if self.rect.w != new_w or self.rect.h != new_h:
                self.rect.w = new_w
                self.rect.h = new_h
                self._calculate_adaptive_size()  # Recalc on resize
        
    def draw(self, surface):
        if not self.visible:
            return
            
        # keep track
        self._calculate_adaptive_size()

        pygame.draw.rect(surface, (30, 30, 40), self.rect)
        
        start_x = self.rect.x
        start_y = self.rect.y
        end_x = self.rect.right
        end_y = self.rect.bottom
        
        # Use adaptive size for grid
        cell_size = self.adaptive_size
        
        for x in range(start_x, end_x, cell_size):
            if (x - start_x) % (cell_size * 5) == 0:
                pygame.draw.line(surface, self.major_tick_color, (x, start_y), (x, end_y), 2)
            else:
                pygame.draw.line(surface, self.grid_color, (x, start_y), (x, end_y), 1)
        
        for y in range(start_y, end_y, cell_size):
            if (y - start_y) % (cell_size * 5) == 0:
                pygame.draw.line(surface, self.major_tick_color, (start_x, y), (end_x, y), 2)
            else:
                pygame.draw.line(surface, self.grid_color, (start_x, y), (end_x, y), 1)
        
        super().draw(surface)

import pygame
from component import Component

class Gauge(Component):
    def __init__(self, x=0, y=0, w=100, h=100, *, min_val=0, max_val=100, value=0, on_update=None):
        super().__init__(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.on_update = on_update
        
    def update(self, dt):
        if self.on_update:
            self.value = self.on_update()
        super().update(dt)
        
    def draw(self, surface):
        if not self.visible:
            return
            
        center_x = self.rect.x + self.rect.w // 2
        center_y = self.rect.y + self.rect.h // 2
        radius = min(self.rect.w, self.rect.h) // 2 - 5
        
        # Draw gauge background
        pygame.draw.circle(surface, (30, 30, 40), (center_x, center_y), radius)
        pygame.draw.circle(surface, (60, 60, 80), (center_x, center_y), radius, 2)
        
        # Draw ticks
        for i in range(0, 11):  # 10 major ticks
            angle = 225 + (i * 27)  # 225° to 495° (270° arc)
            rad = pygame.math.Vector2(1, 0).rotate(angle).normalize()
            
            inner_radius = radius * 0.7 if i % 5 == 0 else radius * 0.8
            outer_radius = radius * 0.9
            
            start_pos = (center_x + rad.x * inner_radius, center_y + rad.y * inner_radius)
            end_pos = (center_x + rad.x * outer_radius, center_y + rad.y * outer_radius)
            
            color = (100, 100, 120) if i % 5 == 0 else (70, 70, 90)
            width = 2 if i % 5 == 0 else 1
            pygame.draw.line(surface, color, start_pos, end_pos, width)
        
        # Draw needle
        if self.max_val > self.min_val:
            normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
            angle = 225 + (normalized * 270)  # 225° to 495°
            rad = pygame.math.Vector2(1, 0).rotate(angle).normalize()
            
            needle_end = (center_x + rad.x * (radius * 0.8), center_y + rad.y * (radius * 0.8))
            pygame.draw.line(surface, (220, 60, 60), (center_x, center_y), needle_end, 3)
        
        # Center pin
        pygame.draw.circle(surface, (180, 180, 200), (center_x, center_y), 4)
        
        super().draw(surface)

class Window(Component):
    def __init__(self, x=100, y=100, w=300, h=200, *, title="Window"):
        super().__init__(x, y, w, h)
        self.theme = get_theme()
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.resizing = False
        self.resize_start = (0, 0)
        self.min_size = (150, 120)
        self.can_resize = False
        self.can_close = False
        self.header = Label(0, 0, w, 25, caption=title)
        self.add_child(self.header)
        self.close_btn = Button("X", w-25, 0, 25, 25, on_click=self.close)
        self.add_child(self.close_btn)
        self.header.focusable = True
        self.bring_to_front()
        

    def close(self, btn, pos):
        if self.can_close:
            if self.parent:
                self.parent.remove_child(self)

    def on_mouse_down(self, button, pos):
        if not self.can_resize:
            return
        local_pos = self.global_to_local(pos)
        
        if button == 0:
            if self.header.rect.collidepoint(local_pos):
                self.dragging = True
                self.drag_offset = (local_pos[0], local_pos[1])
                self.bring_to_front()
                return True
                
            resize_area = pygame.Rect(self.rect.w-20, self.rect.h-20, 20, 20)
            if resize_area.collidepoint(local_pos):
                self.resizing = True
                self.resize_start = (self.rect.w, self.rect.h)
                return True
                
        return False

    def on_drag(self, delta, offset):
        if not self.can_resize:
            return
        if self.dragging:
            self.rect.x += delta[0]
            self.rect.y += delta[1]
            
        elif self.resizing:
            new_w = max(self.min_size[0], self.resize_start[0] + delta[0])
            new_h = max(self.min_size[1], self.resize_start[1] + delta[1])
            self.rect.w, self.rect.h = new_w, new_h
            self.header.rect.w = new_w
            self.close_btn.rect.x = new_w - 25

    def on_drag_end(self, delta, offset):
        if not self.can_resize:
            return
        self.dragging = False
        self.resizing = False

    def on_mouse_enter(self):
        self.header.set_text(f"[{self.title}]")

    def on_mouse_leave(self):
        self.header.set_text(self.title)

    def draw(self, surface):
        if not self.visible:
            return
            
        pygame.draw.rect(surface, (40, 45, 60), self.rect)
        pygame.draw.rect(surface, (60, 70, 100), self.rect, 2)
        
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 25)
        pygame.draw.rect(surface, (70, 80, 110), header_rect)
        pygame.draw.rect(surface, (100, 110, 140), header_rect, 1)
        
        if self.can_resize:
            resize_rect = pygame.Rect(self.rect.right-20, self.rect.bottom-20, 20, 20)
            pygame.draw.rect(surface, (80, 90, 120), resize_rect)
        
        super().draw(surface)
        
        

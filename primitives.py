import pygame
import time
import random
from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable

from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

# Pre-load fonts
pygame.font.init()

# Globals

class Alignment(IntEnum):
    CENTER = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4

class Style(IntEnum):
    NORMAL = 0
    SMALL = 1
    BIG = 2
    
"""    
    Primitive Components
    
"""

# Placeholder component

class Container(Component):
    def __init__(self, x: int = 0, y: int = 0,  width: int = 90, height: int = 45):
        super().__init__(x, y, width, height)
        self.name = 'Container'
        self.filler = True
        self.filler_style = 1
            
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)

# Functional components

class Label(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 100, height: int = 24, text: str = ""):
        super().__init__(x, y, width, height)
        self.name = 'Label'
        self.text = text
        self.padding = 4
        self.text_align = Alignment.LEFT
        self.text_valign = Alignment.CENTER
        self.text_style = Style.NORMAL

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        if self.text:
            if self.text_style == Style.BIG:
                _font = self.fontB
            elif self.text_style == Style.SMALL:
                _font = self.fontS
            else: # fallback
                _font = self.font
                
            text_surf = _font.render(self.text, True, self.fg)
            text_rect = text_surf.get_rect()
            
            abs_rect = self.get_absolute_rect()
            
            # Horizontal alignment
            if self.text_align == Alignment.LEFT:
                text_rect.left = abs_rect.left + self.padding
            elif self.text_align == Alignment.RIGHT:
                text_rect.right = abs_rect.right - self.padding
            else:  # center
                text_rect.centerx = abs_rect.centerx
            
            # Vertical alignment
            if self.text_valign == Alignment.TOP:
                text_rect.top = abs_rect.top + self.padding
            elif self.text_valign == Alignment.BOTTOM:
                text_rect.bottom = abs_rect.bottom - self.padding
            else:  # center
                text_rect.centery = abs_rect.centery
            
            # Clip to bounds
            surface.blit(text_surf, text_rect)
        
        super().draw(surface)

class Icon(Component):
    _image_cache = {}  # Class-level cache: {filename: pygame.Surface}

    def __init__(self, x: int = 0, y: int = 0, width: int = 24, height: int = 24, filename: str = ""):
        super().__init__(x, y, width, height)
        self.name = 'Icon'
        self.filename = ""
        self.scale_factor = 1.0  # 0.0 = no scaling (original size), 1.0 = fit to bounds
        self._image: Optional[pygame.Surface] = None
        if filename:
            self.load(filename)

    def load(self, filename: str) -> bool:
        if not filename:
            self._image = None
            self.filename = ""
            self.reset()
            return False

        # Use cached image if available
        if filename in Icon._image_cache:
            self._image = Icon._image_cache[filename]
        else:
            try:
                path = f"./assets/{filename}"
                img = pygame.image.load(path).convert_alpha()
                Icon._image_cache[filename] = img
                self._image = img
            except Exception as e:
                print(f"Error: failed to load '{filename}': {e}")
                self._image = None
                return False

        self.filename = filename
        self.reset()
        return True

    @property
    def scale(self) -> float:
        return self.scale_factor

    @scale.setter
    def scale(self, value: float):
        value = max(0.0, min(1.0, float(value)))
        if self.scale_factor == value:
            return
        self.scale_factor = value
        self.reset()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or self._image is None:
            return

        abs_rect = self.get_absolute_rect()
        img = self._image

        # Compute target size
        if self.scale_factor <= 0.0:
            # No scaling: draw original at center
            draw_rect = img.get_rect(center=abs_rect.center)
        else:
            # Fit within bounds, preserving aspect ratio
            img_w, img_h = img.get_size()
            if img_w == 0 or img_h == 0:
                return

            # Max available size (with 2px padding)
            max_w = abs_rect.width - 4
            max_h = abs_rect.height - 4
            if max_w <= 0 or max_h <= 0:
                return

            # Compute fit scale
            scale_w = max_w / img_w
            scale_h = max_h / img_h
            fit_scale = min(scale_w, scale_h)

            # Apply user scale (0.0 → no scale, 1.0 → full fit)
            target_scale = self.scale_factor * fit_scale + (1.0 - self.scale_factor) * 1.0
            # But if scale_factor == 0, we want *original* size, not 1.0× — clarify:
            # Actually: 0.0 = draw original (no resize), 1.0 = draw max-fit
            if self.scale_factor == 0.0:
                target_w, target_h = img_w, img_h
            else:
                target_w = int(img_w * fit_scale * self.scale_factor)
                target_h = int(img_h * fit_scale * self.scale_factor)
                # Ensure at least 1×1
                target_w = max(1, target_w)
                target_h = max(1, target_h)

            # Scale image (cache if needed? skip for now — small icons)
            try:
                scaled_img = pygame.transform.smoothscale(img, (target_w, target_h))
            except ValueError:
                # Fallback for 0-size
                return

            draw_rect = scaled_img.get_rect(center=abs_rect.center)
            img = scaled_img

        # Draw
        surface.blit(img, draw_rect)

        # Optional: debug frame
        # self.draw_frame(surface)

        super().draw(surface)

class Button(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 80, height: int = 30, text: str = "OK", ):
        super().__init__(x, y, width, height)
        self.name = 'Button'
        self.text = text
        self.padding = 4
        self.text_align = Alignment.CENTER
        self.text_valign = Alignment.CENTER
        self.text_style = Style.NORMAL
        self.on_click: Optional[Callable[[], None]] = self._null
        
    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                if self.on_click:
                    self.on_click()
                return True
        return consumed

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        abs_rect = self.get_absolute_rect()
        
        # Text
        if self.text:
            font = self.fontB if self.text_style == Style.BIG else \
                   self.fontS if self.text_style == Style.SMALL else \
                   self.font
            
            # Clip text to self bounds (uses active font + padding)
            max_width = self.width - 2 * self.padding
            raw_text = self.text
            text_width = font.size(raw_text)[0]
            
            if text_width > max_width:
                ellipsis = "…"
                ellipsis_w = font.size(ellipsis)[0]
                avail = max(0, max_width - ellipsis_w)
                display = ellipsis
                for i in range(len(raw_text), 0, -1):
                    trial = raw_text[:i]
                    if font.size(trial)[0] <= avail:
                        display = trial + ellipsis
                        break
            else:
                display = raw_text
            
            text_surf = font.render(display, True, self.fg)
            text_rect = text_surf.get_rect()
            
            # Alignment (within self bounds)
            if self.text_align == Alignment.LEFT:
                text_rect.left = abs_rect.left + self.padding
            elif self.text_align == Alignment.RIGHT:
                text_rect.right = abs_rect.right - self.padding
            else:
                text_rect.centerx = abs_rect.centerx
            
            if self.text_valign == Alignment.TOP:
                text_rect.top = abs_rect.top + self.padding
            elif self.text_valign == Alignment.BOTTOM:
                text_rect.bottom = abs_rect.bottom - self.padding
            else:
                text_rect.centery = abs_rect.centery
            
            surface.blit(text_surf, text_rect)
        
        super().draw(surface)
        
    def _null(self) -> None:
        return

# Window Base

class Window(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.can_move = not fixed
        self.filler = True
        self.filler_style = 4
        
    def update(self, dt: float) -> None:
        super().update(dt)
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)
        
    def process_event(self, event: pygame.event.Event) -> bool:
        if not self.can_move:
            return super().process_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hitbox_test(event.pos):
                self.dragging = True
                abs_rect = self.get_absolute_rect()
                self.drag_offset = (event.pos[0] - abs_rect.x, event.pos[1] - abs_rect.y)
                self.bring_to_front()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
                
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_x = event.pos[0] - self.drag_offset[0]
            new_y = event.pos[1] - self.drag_offset[1]
            self.position = (new_x, new_y)
            return True
            
        return super().process_event(event)
    
    # Default dialog pre-states
    
    def click_ok(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_OK,
                data=self
            ))
        self.destroy()
        
    def click_cancel(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_CANCEL,
                data=self
            ))
        self.destroy()
        
    def cycle_theme(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_THEME,
                data=theme
            ))
    
    def toggle_lock(self) -> None:
        self.can_move = not self.can_move
        hoster = self.root()
        if hoster:
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_LOCK,
                data=not self.can_move
            ))
        
    def destroy(self) -> None:
        hoster = self.root()
        if hoster:
            hoster.bus.post(Packet(receiver=BROADCAST,sender=self.address, rs=Response.M_BYE, data=self))
        super().destroy()
    
    def hitbox_test(self, point: tuple[int, int], hitbox_y: int = 0) -> bool:
        """Check if click is within header area"""
        if not self.is_inside(point):
            return False
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < self.height - hitbox_y
        
            
# Window Builders

class WindowBase:
    def __init__(self, engine: Component):
        self.window = None
        self.engine = engine
        self.header = 0
        self.footer = 0
        
    def create(self, x: int = 0, y: int = 0, width: int = 400, height: int = 300) -> 'WindowBase':
        self.window = Window(x ,y, width, height)
        self.window.can_close = True
        self.window.passthrough = False
        return self
    
    def build(self) -> 'WindowBase':
        if hasattr(self.engine, 'bus'):
            self.engine.add(self.window)
            self.engine.bus.post(Packet(receiver=BROADCAST,sender=self.window.address, rs=Response.M_PING, data=True))
        else:
            print('Warning: missing messenger')
        return self

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.tag = ""
        self.header = 24
        self.padding = 4
        self.components = {}

    def as_dialog(self, title: str) -> 'Gui':
        self.tag = title
        if self.window:
            # icon
            c_icon = Icon(0, 0, self.header, self.header, 'window.png')
            c_icon.name = 'Icon'
            c_icon.passthrough = True
            self.components['icon'] = c_icon
            self.window.add(c_icon)
            
            # title caption
            c_label = Label(self.header, 0, 1, self.header, self.tag)
            c_label.passthrough = True
            c_label.text_align = Alignment.LEFT
            c_label.text_valign = Alignment.CENTER
            c_label.text_style = Style.BIG
            self.components['label'] = c_label
            self.window.add(c_label)
            
            # finalize layout
            self._layout_dialog()
        return self

    def _layout_dialog(self) -> None:
        if not self.window or 'icon' not in self.components:
            return
        c_icon = self.components['icon']
        c_label = self.components['label']
        
        c_icon.size = (self.header, self.header)
        c_icon.position = (0, 0)
        
        c_label.position = (self.header, 0)
        c_label.size = (self.window.width - self.header, self.header)
        
        if 'button_ok' not in self.components:
            btn_ok = Button(self.window.width - 120, self.window.height - 30, 60, 30, 'OK')
            btn_ok.name = 'button_ok'
            btn_ok.on_click = self.window.click_ok
            self.components['button_ok'] = btn_ok
            self.window.add(btn_ok)
        if 'button_cancel' not in self.components:
            btn_cancel = Button(self.window.width - 60, self.window.height - 30, 60, 30, 'CANCEL')
            btn_cancel.name = 'button_cancel'
            btn_cancel.on_click = self.window.click_cancel
            self.components['button_cancel'] = btn_cancel
            self.window.add(btn_cancel)
        if 'information' not in self.components:
            c_msg = Container(0, 0, 1, 1)
            c_msg.name = 'information'
            c_msg.passthrough = True
            self.components['information'] = c_msg
            self.window.add(c_msg)
            
        # Reposition
        btn_ok.position = (self.window.width - 120-self.padding, self.window.height - 30-self.padding)
        btn_cancel.position = (self.window.width - 60-self.padding, self.window.height - 30-self.padding)
        usable_height = self.window.height - self.header - btn_ok.height - 2 * self.padding
        usable_width = self.window.width - 2 * self.padding
        c_msg.size = (usable_width, max(1, usable_height))
        c_msg.position = (self.padding, self.header + self.padding)
        
        # Register components
        if hasattr(self.engine, 'bus'):
            self.engine.bus.register(c_icon)
            self.engine.bus.register(c_label)
            self.engine.bus.register(btn_ok)
            self.engine.bus.register(btn_cancel)
            self.engine.bus.register(c_msg)

    def reset(self) -> None:
        self._layout_dialog()
        if self.parent:
            self.parent.reset()
        else:
            self.window.reset()

    def set_theme(self, base_hue: int = None) -> 'Gui':
        if hasattr(self.engine, 'bus'):
            theme = self.window.new_theme(base_hue)
            self.engine.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.window.address,
                rs=Response.M_THEME,
                data=theme
            ))
        return self
        
    
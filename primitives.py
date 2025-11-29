import pygame
import time
import random
from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable

from component import Component
from bus import BROADCAST, MASTER, Response, Packet, AddressBus

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
        self.filler_style = 0
            
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)

# Functional components

class Label(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 100, height: int = 24, text: str = "",
                 align: Alignment = Alignment.LEFT, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.NORMAL):
        super().__init__(x, y, width, height)
        self.name = 'Label'
        self._text = ""
        self.padding = 4
        self.text_align = align
        self.text_valign = valign
        self.text_style = style
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
        self.text = text
        self.filler = True
        self.filler_style = 4

    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str):
        value = str(value) if value else ""
        if self._text == value:
            return
        self._text = value
        self.reset()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        # filler first
        super().draw(surface)
        
        # text last
        if self.text:
            text_surf = self._font.render(self.text, True, self.fg)
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
        
        

class MultiLabel(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 100, text: str = "",
                 align: Alignment = Alignment.CENTER, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.NORMAL):
        super().__init__(x, y, width, height)
        self.name = 'MultiLabel'
        self._text = ""
        self._lines = []
        self.padding = 2
        self.line_spacing = 2
        self.text_align = align
        self.text_valign = valign
        self.text_style = style
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
        self.text = text
        self.filler = True
        self.filler_style = 0

    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str):
        value = str(value) if value else ""
        if self._text == value:
            return
        self._text = value
        self._update_lines()
        self.reset()

    def _update_lines(self) -> None:
        """Precompute wrapped lines — called only on text/size change"""
        self._lines = []
        if not self._text:
            return

        avail_width = max(0, self.width - 2 * self.padding)
        if avail_width <= 0:
            return

        # Split into paragraphs (preserve \n)
        paragraphs = self._text.split('\n')
        for para in paragraphs:
            if not para:
                self._lines.append("")
                continue
            words = para.split(' ')
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if self._font.size(test_line)[0] <= avail_width:
                    line = test_line
                else:
                    if line:
                        self._lines.append(line)
                    line = word  # start new line
            if line:
                self._lines.append(line)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or not self._lines:
            return
        # filler first
        super().draw(surface)
        
        # text last
        abs_rect = self.get_absolute_rect()
        line_height = self._font.get_height() + self.line_spacing

        # Vertical start (respect valign)
        total_text_height = len(self._lines) * line_height - self.line_spacing
        if self.text_valign == Alignment.TOP:
            y = abs_rect.top + self.padding
        elif self.text_valign == Alignment.BOTTOM:
            y = abs_rect.bottom - self.padding - total_text_height
        else:  # center
            y = abs_rect.centery - total_text_height // 2

        # Clip rendering to self bounds
        old_clip = surface.get_clip()
        try:
            surface.set_clip(abs_rect)
            for line in self._lines:
                if y + line_height < abs_rect.top:
                    y += line_height
                    continue  # skip off-top lines
                if y > abs_rect.bottom:
                    break    # stop at bottom

                # Render line
                text_surf = self._font.render(line, True, self.fg)
                text_rect = text_surf.get_rect()

                if self.text_align == Alignment.LEFT:
                    text_rect.left = abs_rect.left + self.padding
                elif self.text_align == Alignment.RIGHT:
                    text_rect.right = abs_rect.right - self.padding
                else:  # center
                    text_rect.centerx = abs_rect.centerx

                text_rect.top = y
                surface.blit(text_surf, text_rect)
                y += line_height
        finally:
            surface.set_clip(old_clip)

class Button(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 80, height: int = 30, text: str = "OK",
                 align: Alignment = Alignment.CENTER, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.SMALL):
        super().__init__(x, y, width, height)
        self.name = 'Button'
        self.filler = False
        self.filler_style = 0
        self.text = text
        self.padding = 4
        self.text_style = style
        self.text_align = align
        self.text_valign = valign
        self.on_click: Optional[Callable[[], None]] = self._null
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
                         
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
        if self.text:
            # Clip text to self bounds (uses active font + padding)
            max_width = self.width - 2 * self.padding
            raw_text = self.text
            text_width = self._font.size(raw_text)[0]
            
            if text_width > max_width:
                ellipsis = "…"
                ellipsis_w = self._font.size(ellipsis)[0]
                avail = max(0, max_width - ellipsis_w)
                display = ellipsis
                for i in range(len(raw_text), 0, -1):
                    trial = raw_text[:i]
                    if self._font.size(trial)[0] <= avail:
                        display = trial + ellipsis
                        break
            else:
                display = raw_text
            
            text_surf = self._font.render(display, True, self.fg)
            text_rect = text_surf.get_rect()
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
        self.filler_style = 0
        self.border = True
        
        
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
                sender=0, # root
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
            hoster.bus.post(Packet(receiver=hoster.address,sender=self.address, rs=Response.M_BYE, data=self))
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
            print('Warning: missing bus messenger instance')
        return self

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.tag = ""
        self.header = 24
        self.padding = 4
        self.content = None
        self.components = {}

    def as_dialog(self, title: str, message: str) -> 'Gui':
        self.tag = title
        self.content = message
        if self.window:
            # icon
            c_icon = Container(0, 0, self.header, self.header)
            c_icon.name = 'Icon'
            c_icon.passthrough = True
            c_icon.border = True
            self.components['icon'] = c_icon
            self.window.add(c_icon)
            
            # title caption
            c_label = Label(self.header, 0, 1, self.header, self.tag, 
                            Alignment.LEFT, Alignment.CENTER, Style.BIG)
            c_label.passthrough = True
            c_label.border = True
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
            btn_ok = Button(self.window.width - 120, self.window.height - 30, 60, 30, 'OK',
                            Alignment.CENTER, Alignment.CENTER, Style.SMALL)
            btn_ok.name = 'button_ok'
            btn_ok.border = True
            btn_ok.on_click = self.window.click_ok
            self.components['button_ok'] = btn_ok
            self.window.add(btn_ok)
        if 'button_cancel' not in self.components:
            btn_cancel = Button(self.window.width - 60, self.window.height - 30, 60, 30, 'CANCEL',
                                Alignment.CENTER, Alignment.CENTER, Style.SMALL)
            btn_cancel.name = 'button_cancel'
            btn_cancel.border = True
            btn_cancel.on_click = self.window.cycle_theme#self.window.click_cancel
            self.components['button_cancel'] = btn_cancel
            self.window.add(btn_cancel)
        if 'information' not in self.components:
            c_msg = MultiLabel(0, 0, 1, 1, '',
                               Alignment.LEFT, Alignment.CENTER, Style.SMALL)
            c_msg.name = 'information'
            c_msg.passthrough = True
            self.components['information'] = c_msg
            self.window.add(c_msg)
            
        # Final update & reposition
        btn_ok.position = (self.window.width - 120-self.padding, self.window.height - 30-self.padding)
        btn_cancel.position = (self.window.width - 60-self.padding, self.window.height - 30-self.padding)
        usable_height = self.window.height - self.header - btn_ok.height - 2 * self.padding
        usable_width = self.window.width - 2 * self.padding
        c_msg.size = (usable_width, max(1, usable_height))
        c_msg.position = (self.padding, self.header + self.padding)
        c_msg.text = self.content
        
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
                sender=MASTER,
                rs=Response.M_THEME,
                data=theme
            ))
        return self
        
    
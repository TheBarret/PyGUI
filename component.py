import pygame
from typing import Optional, Tuple, Dict, Callable, Any, List, Set, TYPE_CHECKING
from bus import BROADCAST, Response, Packet, AddressBus
from chain import Dispatcher, Messenger, Theme

if TYPE_CHECKING:
    from component import Component

class Component(Dispatcher, Messenger, Theme):
    def __init__(self, x: int = 0, y: int = 0, width: int = 128, height: int = 64):
        # initializers
        self.rect = pygame.Rect(x, y, max(1, width), max(1, height))
        Theme.__init__(self)
        Dispatcher.__init__(self)
        Messenger.__init__(self)
        
    # FALLBACK
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if self.filler:
            self.fill_region(surface, self.filler_style)
        self.draw_frame(surface)
        super().draw(surface)
    
    # MANAGEMENT
    
    def add(self, child: 'Component') -> None:
        if child.parent: 
            child.parent.remove(child)
        self.children.append(child)
        child.parent = self
        self.reset()
    
    def remove(self, child: 'Component') -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.reset()
    
    def root(self) -> 'Component':
        if not hasattr(self, '_root_cache'):
            self._root_cache = self if self.parent is None else self.parent.root()
        return self._root_cache
    
    def destroy(self) -> None:
        for child in self.children[:]: 
            child.destroy()
        self.children.clear()
        self.parent = None
        self.terminated = True
        self.rect = pygame.Rect(self.rect.x, self.rect.y, 1, 1)
    
    def reset(self) -> None:
        self.redraw = True
        if self.parent: 
            self.parent.reset()

    def reset_cache(self):
        if hasattr(self, '_root_cache'):
            del self._root_cache
        for child in self.children:
            child.reset_cache()
    
    def bring_to_front(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            self.parent.children.append(self)
            self.parent.reset()
    
    def send_to_back(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            self.parent.children.insert(0, self)
            self.parent.reset()

    # QOL UTILITIES
    
    def get_absolute_rect(self) -> pygame.Rect:
        x, y = self.rect.topleft
        parent = self.parent
        while parent:
            x += parent.rect.x
            y += parent.rect.y
            parent = parent.parent
        return pygame.Rect(x, y, self.rect.width, self.rect.height)
    
    def clip_text(self, font: pygame.font.Font, text: str, padding: int = 1) -> str:
        # TODO: 
        # check if 'text' length won't exceed self.rect bounds
        # if false:
        #   - return text untouched
        # else:
        #   - measure and cut at what character we have overflow
        #   - use padding to set a soft bound to avoid font glyph clipping
        #   - return reduced sequence, add cosmetic tail  '...'
        return text

    # PROPERTIES
    @property
    def x(self) -> int: return self.rect.x
    @x.setter
    def x(self, value: int): self.rect.x = value; self.reset()
    
    @property
    def y(self) -> int: return self.rect.y
    @y.setter
    def y(self, value: int): self.rect.y = value; self.reset()
    
    @property
    def width(self) -> int: return self.rect.width
    @width.setter
    def width(self, value: int): self.rect.width = max(1, value); self.reset()
    
    @property
    def height(self) -> int: return self.rect.height
    @height.setter
    def height(self, value: int): self.rect.height = max(1, value); self.reset()
    
    @property
    def position(self) -> Tuple[int, int]: return (self.rect.x, self.rect.y)
    @position.setter
    def position(self, value: Tuple[int, int]): self.rect.x, self.rect.y = value; self.reset()
    
    @property
    def size(self) -> Tuple[int, int]: return (self.rect.width, self.rect.height)
    @size.setter
    def size(self, value: Tuple[int, int]): 
        self.rect.width, self.rect.height = max(1, value[0]), max(1, value[1])
        self.reset()
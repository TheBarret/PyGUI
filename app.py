import pygame
import time
from typing import List, Tuple 
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

# ─── Engine ───────────────────────────────────────────────────────────


class Engine(Component):
    def __init__(self, width: int = 800, height: int = 600, fps: int = 60, title: str = "Engine"):
        super().__init__(0, 0, width, height)
        pygame.init()
        pygame.display.set_caption(title)
        self.name = "engine"
        self.clock = pygame.time.Clock()
        self.surface: pygame.Surface = pygame.display.set_mode((width, height), 0)
        self.dt = 0.0
        self.fps = fps
        self.running = False
        self.bus = AddressBus()
        self.bus.register(self)
        
    def root(self) -> 'Component':
        return self
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
    
    def add(self, child: 'Component') -> None:
        super().add(child)
        self.bus.register(child)
        
    def remove(self, child: 'Component') -> None:
        super().remove(child)
        self.bus.unregister(child)
        
    def run(self) -> None:
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.destroy()
                    continue
                self.handle_event(event)
            self.dt = self.clock.tick(self.fps) / 1000.0
            self.bus.pump()
            self.update(self.dt)
            self.surface.fill((0, 0, 0))
            self.draw(self.surface)
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return True
        return super().handle_event(event)

    def destroy(self) -> None:
        self.running = False
        super().destroy()

# ─── Components ───────────────────────────────────────────────────────────


class Lister(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150):
        super().__init__(x, y, width, height)
        self.name = 'Lister'
        self.passthrough_events = True
        self.lines = []
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 12)
        sample = self.font.render("abc", True, (255, 255, 255))
        self.line_height = sample.get_height() + 2
        self.max_lines = height // self.line_height
        self.column_width = 50
        self.bg_color = pygame.Color(30, 30, 40)
        self.text_color = pygame.Color(220, 220, 220)
        self.colors = {
            'INFO': pygame.Color(180, 180, 200),
            'API': pygame.Color(255, 255, 100), 
            'ERROR': pygame.Color(255, 100, 100)
        }

    def write(self, text: str, event: str = 'INFO') -> None:
        self.lines.append((event, str(text)))
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        self.reset()
    
    def clear(self) -> None:
        self.lines.clear()
        self.reset()
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg_color, abs_rect)
        pygame.draw.rect(surface, (100, 100, 120), abs_rect, 1)
        
        # Draw column separator
        sep_x = abs_rect.x + self.column_width
        pygame.draw.line(surface, (80, 80, 100), (sep_x, abs_rect.y), (sep_x, abs_rect.bottom), 1)
        
        # Draw text lines with columns
        y_offset = abs_rect.bottom - (len(self.lines) * self.line_height)
        max_msg_width = abs_rect.width - self.column_width - 10  # Available width for messages
        
        for i, (msg_type, line) in enumerate(self.lines):
            text_y = y_offset + (i * self.line_height)
            
            # Only draw if within bounds
            if text_y + self.line_height >= abs_rect.y:
                # Draw type in first column
                type_color = self.colors.get(msg_type, self.text_color)
                type_surface = self.font.render(msg_type, True, type_color)
                surface.blit(type_surface, (abs_rect.x + 5, text_y))
                
                # Draw message in second column (with clipping)
                msg_width = self.font.size(line)[0]
                if msg_width > max_msg_width:
                    # Find where to clip
                    for clip_pos in range(len(line), 0, -1):
                        clipped = line[:clip_pos] + "..."
                        if self.font.size(clipped)[0] <= max_msg_width:
                            line = clipped
                            break
                
                msg_surface = self.font.render(line, True, self.text_color)
                surface.blit(msg_surface, (sep_x + 5, text_y))
        
        super().draw(surface)

class Panel(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150):
        super().__init__(x, y, width, height)
        self.name = 'Panel'


    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        src_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, (72, 72, 72), src_rect)
        pygame.draw.rect(surface, (172, 172, 172), src_rect, 1)
        
        super().draw(surface)

    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
        
class Window(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window'):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        self.dragging = False
        self.drag_offset = (0, 0)
        
    def initialize(self) -> None:
        # setup component stack
        header = Panel(0, 0, self.width, 30)
        header.name = 'Header'
        header.passthrough = True
        body = Panel(0, 30, self.width, self.height - 30)
        body.name = 'Body'
        body.passthrough = True
        self.debugger = Lister(0, header.rect.h, self.rect.w, self.rect.h)
        self.debugger.name = 'Debugger'
        self.debugger.passthrough = True
        self.add(header)
        self.add(body)
        self.add(self.debugger)
        self.debugger.bring_to_front()
        self.debugger.write(f'Initialized')
        self.debugger.write(f'  container : {self.name}')
        self.debugger.write(f'  root      : {self.root().name}')
        self.debugger.write(f'  rect      : {self.rect}')
        
        # setup bus routing
        hoster = self.root()
        if hoster and hasattr(hoster, 'bus'):
            hoster.bus.register(header)
            hoster.bus.register(body) 
            hoster.bus.register(self.debugger)
            hoster.bus.post(Packet(receiver=BROADCAST,sender=self.address, rs=Response.M_PING, data=True))
            self.debugger.write(f'Listening for components...')
    
    def process_event(self, event: pygame.event.Event) -> bool:
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
            
        # pass on
        return super().process_event(event)
    
    def hitbox_test(self, point: tuple[int, int]) -> bool:
        """Check if click is within header area (top 30 pixels of window)"""
        if not self.is_inside(point):
            return False
            
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < 30  # Header height
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        # Draw window background
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, (50, 50, 60), abs_rect)
        pygame.draw.rect(surface, (100, 100, 120), abs_rect, 2)
        
        # Draw header highlight when dragging
        if self.dragging:
            header_rect = pygame.Rect(abs_rect.x, abs_rect.y, abs_rect.width, 30)
            pygame.draw.rect(surface, (80, 80, 100), header_rect)
        
        # Draw children (header and body panels)
        super().draw(surface)
                        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_PONG:
            now = time.time()
            rtt = now - msg.data["timestamp"]
            rtt_ms = rtt * 1000
            self.debugger.write(f'Reply from 0x{msg.data["address"]:02x} ({msg.data["name"]}) - {rtt_ms:.1f}ms', 'API')
        super().handle_message(msg)
        
# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(800, 600, 60)
    desktop = Window(10, 200, 800-10, 300)
    init.add(desktop)
    desktop.initialize()
    
    init.run()
    
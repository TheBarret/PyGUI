import time
import pygame
import random
from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable, Optional

from component import Component
from bus import BROADCAST, MASTER, Response, Packet, AddressBus

       
class Blinker(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 12):
        super().__init__(x, y, width, height)
        self.name = 'Blinker'
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        self.activity_timeout = 0.1  # How long to show activity (seconds)
        self.activity_timer = 0.0
        self.is_active = False
        self.active_color = pygame.Color(255, 0, 0)  # Red
        self.inactive_color = pygame.Color(0, 0, 0)  # Black
        self.normal_bg = self.bg  # Store original background
        self._setup_indicator()
    
    def _setup_indicator(self):
        """Initialize the indicator state"""
        self.bg = self.inactive_color
        self.redraw = True
    
    def handle_message(self, msg: Packet) -> None:
        """React to any incoming message"""
        super().handle_message(msg)
        self._trigger_activity()
    
    def _trigger_activity(self):
        """Trigger the activity indicator"""
        self.is_active = True
        self.bg = self.active_color
        self.activity_timer = self.activity_timeout
        self.redraw = True
    
    def update(self, dt: float) -> None:
        """Update the indicator state"""
        super().update(dt)
        
        if self.is_active:
            self.activity_timer -= dt
            if self.activity_timer <= 0:
                self.is_active = False
                self.bg = self.inactive_color
                self.redraw = True
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        # Draw the activity indicator
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        if self.border:
            pygame.draw.rect(surface, self.fg, abs_rect, 1)

class Pulsar(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 12):
        super().__init__(x, y, width, height)
        self.name = 'Pulsar'
        self.filler = False
        self.border = True
        self.border_style = 0
        self.activity_timeout = 0.15
        self.activity_timer = 0.0
        self.is_active = False
        self.pulse_phase = 0.0
        self.pulse_speed = 15.0
        self.base_color = pygame.Color(255, 0, 0)  # Base red
        self.redraw = True
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
        self._trigger_activity()
    
    def _trigger_activity(self):
        self.is_active = True
        self.activity_timer = self.activity_timeout
        self.pulse_phase = 0.0
        self.redraw = True
    
    def update(self, dt: float) -> None:
        super().update(dt)
        
        if self.is_active:
            self.activity_timer -= dt
            self.pulse_phase += dt * self.pulse_speed
            
            if self.activity_timer <= 0:
                self.is_active = False
            self.redraw = True
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        
        # Calculate pulse intensity (0.0 to 1.0)
        if self.is_active:
            pulse_intensity = min(1.0, self.pulse_phase) if self.pulse_phase < 1.0 else 1.0
            # Fade out as timer decreases
            fade_factor = max(0.0, self.activity_timer / self.activity_timeout)
            pulse_intensity *= fade_factor
        else:
            pulse_intensity = 0.0
        
        # Create pulsing color
        r = int(self.base_color.r * pulse_intensity)
        g = int(self.base_color.g * pulse_intensity)
        b = int(self.base_color.b * pulse_intensity)
        pulse_color = pygame.Color(r, g, b)
        
        # Draw the indicator
        if pulse_intensity > 0:
            pygame.draw.rect(surface, pulse_color, abs_rect)
        else:
            # Draw a dim indicator when not active
            dim_color = pygame.Color(30, 30, 30)
            pygame.draw.rect(surface, dim_color, abs_rect)
        
        if self.border:
            pygame.draw.rect(surface, self.fg, abs_rect, 1)

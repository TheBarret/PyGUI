import pygame
import time
import random
from typing import List, Any, Dict, Tuple, Callable

from component import Component                                                 # atom base
from primitives import Alignment, Style                                         # globals
from primitives import Label, MultiLabel, Button, Toolbar, Slider               # components
from window import Window                                                       # managers
from utilities import Blinker, Pulsar                                           # widgets

from bus import BROADCAST, MASTER, Response, Packet, AddressBus

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
        else:
            print('Warning: missing bus messenger instance')
        return self

    def ping(self) -> 'WindowBase':
        self.engine.send_ping()
        return self

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.title = ""
        self.header_height = 24
        self.toolbar = None
        self.toolbar_button_width = 25
        self.components = {}
        
    def as_window(self, title: str) -> 'Gui':
        self.title = title
        if self.window:
            self._create_window_header()
        return self

    def with_toolbar(self, divisor: int = 1) -> 'Gui':
        if self.window:
            if divisor < 1: divisor = 1
            self.toolbar_button_width = (self.window.width*0.9)//divisor
            self.toolbar = Toolbar(0, self.header_height, self.window.width, self.header_height,
                                   Alignment.CENTER, Alignment.CENTER)
            self.toolbar.name = 'toolbar'
            self.toolbar.passthrough = False
            self.toolbar.border = True
            self.components['toolbar'] = self.toolbar
            self.window.add(self.toolbar)
        return self
    
    def add_control(self) -> 'Gui':
        """Add common toolbar controls: close, theme, etc."""
        if self.window and self.toolbar:
            # buttons
            #close_btn = self._create_toolbar_button('X', self.window.destroy, 'close')
            label_1 = self._create_toolbar_label('Hue','label1')
            widget_1 = self._create_toolbar_cycle_theme_widget('widget1')
            label_2 = self._create_toolbar_label('Contrast','label2')
            widget_2 = self._create_toolbar_contrast_widget('widget2')
            # store
            self.toolbar.add(label_1)
            self.toolbar.add(widget_1)
            self.toolbar.add(label_2)
            self.toolbar.add(widget_2)
        return self
    
    def add_toolbar_button(self, text: str, callback: Callable, name_suffix: str = "") -> 'Gui':
        """Add a custom button to the toolbar"""
        if self.window and self.toolbar:
            button = self._create_toolbar_button(text, callback, name_suffix)
            self.toolbar.add(button)
        return self
        
    def _create_toolbar_cycle_theme_widget(self, name_suffix: str = "") -> Component:
        pul = Slider(0, 0, self.toolbar_button_width, self.header_height,
                    0, 360, 360//2, self.window.cycle_theme)
        pul.name = f'widget_{name_suffix}' if name_suffix else f'widget_{text.lower()}'
        pul.passthrough = True
        return pul
        
    def _create_toolbar_contrast_widget(self, name_suffix: str = "") -> Component:
        pul = Slider(0, 0, self.toolbar_button_width, self.header_height,
                    0, 100, 50, self.window.cycle_contrast)
        pul.name = f'widget_{name_suffix}' if name_suffix else f'widget_{text.lower()}'
        pul.passthrough = True
        return pul
    
    def _create_toolbar_label(self, caption: str, name_suffix: str = "") -> Component:
        pul = Label(0, 0, self.toolbar_button_width, self.header_height, caption,
                    Alignment.LEFT, Alignment.CENTER, Style.SMALL)
        pul.name = f'label_{name_suffix}' if name_suffix else f'label_{text.lower()}'
        pul.passthrough = True
        pul.border = False
        pul.filler = False
        return pul
        
    def _create_toolbar_button(self, text: str, callback: Callable, name_suffix: str = "") -> Button:
        """Internal method to create standardized toolbar buttons"""
        button = Button(
            0, 0, self.header_height, self.header_height, text,
            Alignment.CENTER, Alignment.CENTER, Style.SMALL
        )
        button.name = f'button_{name_suffix}' if name_suffix else f'button_{text.lower()}'
        button.passthrough = False
        button.on_click = callback
        button.border = True
        return button
    
    def _create_window_header(self) -> None:
        """Create the standard window header components"""
        # Icon button
        icon_btn = Button(
            0, 0, self.header_height, self.header_height, '#',
            Alignment.CENTER, Alignment.CENTER, Style.BIG
        )
        icon_btn.name = 'icon'
        icon_btn.passthrough = False
        icon_btn.on_click = self.window.toggle_lock
        icon_btn.border = True
        icon_btn.border_style = 1
        
        # Title label
        title_label = Label(
            self.header_height, 0, 1, self.header_height, self.title,
            Alignment.LEFT, Alignment.CENTER, Style.BIG
        )
        title_label.passthrough = True
        title_label.border = True
        title_label.border_style = 1
        
        self.components.update({
            'icon': icon_btn,
            'title_label': title_label
        })
        
        self.window.add(icon_btn)
        self.window.add(title_label)
    
    def finalize(self) -> 'Gui':
        """Finalize the window setup - layout and registration"""
        if not self.window:
            return self
            
        self._layout_window_header()
        self._register_components()
        return self
    
    def _layout_window_header(self) -> None:
        """Position the header components"""
        icon = self.components['icon']
        title_label = self.components['title_label']
        
        icon.size = (self.header_height, self.header_height)
        icon.position = (0, 0)
        
        title_label.position = (self.header_height, 0)
        title_label.size = (self.window.width - self.header_height, self.header_height)
    
    def _register_components(self) -> None:
        """Register all components with the bus"""
        for name, component in self.components.items():
            if name not in ['toolbar'] or not self.toolbar:
                self.engine.bus.register(component)
        if self.toolbar:
            self.toolbar.register_all(self.engine.bus)
    
    # Override
    def reset(self) -> 'Gui':
        self._layout_window_header()
        if self.window and self.window.parent:
            self.window.parent.reset()
        elif self.window:
            self.window.reset()
        return self

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
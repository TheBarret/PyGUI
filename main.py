import time
import pygame
from typing import Optional, Callable
from component import Component
from shell import Shell
from ioman import InputManager
from widgets import Label, Image, Button, Overlay, Gauge, Window

# PyGame GUI 1.0 prototype

class App:
    """
    Foundation:
    - Core Foundation (component.py): Hierarchical atom component system
    - Application Layer (main.py): Game loop and lifecycle management
    - Container System (shell.py): Window/workflow management
    - Input Pipeline (ioman.py): Sophisticated event routing
    - Widget Library (widgets.py): Reusable UI tiered components
    - Styling System (theme.py): Consistent visual design
    
    Main application class - handles window, event loop, and subsystems.
    - Fixed timestep updates (tick_rate) with variable rendering
    - Centralized input management via InputManager
    - Component tree lifecycle management
    
    Per frame:
    1. Measure time delta (dt)
    2. Accumulate dt
    3. Process input (once per frame)
    4. Update input manager deltas (once per frame)
    5. While accumulated >= tick_rate:
       - Update game state with fixed tick_rate
       - Subtract tick_rate from accumulator
    6. Render current state (interpolation optional)
    7. Limit FPS
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "App",
        *,
        resizable: bool = False,
        fullscreen: bool = False,
        vsync: bool = True,
        target_fps: int = 60,
        tick_rate: float = 1.0 / 60.0,
    ):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(title)

        # ─── Window Setup ────────────────────────────────────────────────────
        flags = pygame.SCALED
        if resizable:
            flags |= pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN

        self.surface = pygame.display.set_mode((width, height), flags, vsync=vsync)
        self.clock = pygame.time.Clock()

        # ─── Timing Configuration ────────────────────────────────────────────
        self.target_fps = target_fps
        self.tick_rate = tick_rate  # Fixed timestep for updates
        self.accumulated = 0.0

        # ─── Core Subsystems ─────────────────────────────────────────────────
        self.root: Optional[Component] = None
        self.io: Optional[InputManager] = None
        self.running = False

        # ─── Event Hooks ─────────────────────────────────────────────────────
        self.on_quit: Optional[Callable[[], None]] = None
        self.on_resize: Optional[Callable[[int, int], None]] = None

    # ─── Initialization ──────────────────────────────────────────────────────

    def set_root(self, root: Component, debug: Callable[[str], None]) -> None:
        """
        Attach root component tree and initialize subsystems.
        Must be called before run().
        """
        if self.root is not None:
            self.root._unmount()

        self.root = root
        self.io = InputManager(debug)
        root._mount()

    # ─── Event Processing ────────────────────────────────────────────────────

    def _handle_pygame_events(self) -> bool:
        """
        Process all pygame events for this frame.
        Returns False if quit requested.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.WINDOWRESIZED:
                w, h = event.x, event.y
                # Notify callback
                if self.on_resize:
                    self.on_resize(w, h)
                # Resize root to match window
                if self.root:
                    self.root.rect.w, self.root.rect.h = w, h

            else:
                # Route to input manager
                if self.io and self.root:
                    self.io.process_event(event, self.root)

        return True

    # ─── Main Loop ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Main game loop with fixed timestep updates.
        Blocks until app exits.
        """
        if self.root is None:
            raise RuntimeError("No root component set (app.set_root)")
        if self.io is None:
            raise RuntimeError("No input manager initialized")

        self.running = True
        frame_start = time.perf_counter()

        while self.running:
            # ─── Timing ──────────────────────────────────────────────────────
            now = time.perf_counter()
            dt = now - frame_start
            frame_start = now
            self.accumulated += dt
            # ─── Input ───────────────────────────────────────────────────────
            if not self._handle_pygame_events():
                break

            # Reset frame deltas before processing events
            self.io.update(self.root)

            # ─── Fixed Timestep Updates ──────────────────────────────────────
            # Process updates in fixed increments for determinism
            updates = 0
            max_updates = 5  # Prevent spiral of death
            while self.accumulated >= self.tick_rate and updates < max_updates:
                self.root.update(self.tick_rate)
                self.accumulated -= self.tick_rate
                updates += 1

            # If we hit max updates, reset accumulator to prevent catch-up spiral
            if updates >= max_updates:
                self.accumulated = 0.0

            # ─── Render ──────────────────────────────────────────────────────
            self.surface.fill((10, 10, 15))
            self.root.draw(self.surface)
            pygame.display.flip()

            # ─── Frame Rate Limiting ─────────────────────────────────────────
            self.clock.tick(self.target_fps)

        # ─── Cleanup ─────────────────────────────────────────────────────────
        self.root._unmount()
        if self.on_quit:
            self.on_quit()
        pygame.quit()

    def quit(self) -> None:
        """Request graceful shutdown. Will exit on next frame."""
        self.running = False


# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App(width=800, height=600, title="Application",
        resizable=True, vsync=True,
        target_fps=60, tick_rate=1.0 / 60.0
    )
    
    shell = Shell(x=0, y=0, w=800, h=600, resizable=False)
    workspace = Window(x=0, y=0, w=800, h=500, title="Workspace")
    overlay = Overlay(x=0, y=25, w=800, h=500, cell_size=7)
    fps = Gauge(x=0, y=25, w=64, h=64, min_val=0, max_val=120, value=0, on_update=lambda: app.clock.get_fps())
    workspace.add_child(overlay)
    workspace.add_child(fps)
    shell.add_child(workspace)
    
    app.set_root(shell, shell.write)
    
    app.run()
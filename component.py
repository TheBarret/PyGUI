import pygame
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from component import Component


class Component:
    """
    Base atomic UI element.
    - Has rect (position & size) in *parent space*.
    - Supports nesting (children), event handling, and basic lifecycle.
    - Designed for KISS: no auto layout, no forced reactivity — just raw control.
    """

    def __init__(self, x: int = 0, y: int = 0, w: int = 100, h: int = 30):
        # Local geometry: rect is *always* relative to parent (if any)
        self.rect = pygame.Rect(x, y, w, h)
        self.visible = True
        self.enabled = True  # can be clicked/interacted with

        # Parent-child linkage (None = root-level)
        self.parent: Optional['Component'] = None
        self.children: List['Component'] = []

        # State flags (for prototyping convenience)
        self.hovered = False
        self.focused = False
        self.dragging = False

        # Lifecycle mount state
        self._mounted = False

    # ─── Coordinate Transforms ───────────────────────────────────────────────

    def local_to_global(self, local_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert point from *this* local space → global (screen) space."""
        gx, gy = local_pos
        current = self
        while current is not None:
            gx += current.rect.x
            gy += current.rect.y
            current = current.parent
        return gx, gy

    def global_to_local(self, global_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert point from global."""
        lx, ly = global_pos
        
        # Walk up parent chain and subtract each parent's position
        parents = []
        current = self.parent
        while current is not None:
            parents.append(current)
            current = current.parent
        
        # Apply transforms from root down to immediate parent
        for parent in reversed(parents):
            lx -= parent.rect.x
            ly -= parent.rect.y
        
        return lx, ly

    def contains_local(self, local_pos: Tuple[int, int]) -> bool:
        """Does this component's rect contain `local_pos` (in its own space)?"""
        return self.rect.collidepoint(local_pos)

    def contains_global(self, global_pos: Tuple[int, int]) -> bool:
        """Does this component contain `global_pos` (screen space)?"""
        local = self.global_to_local(global_pos)
        return self.contains_local(local)

    # ─── Hierarchy Management ────────────────────────────────────────────────

    def add_child(self, child: 'Component') -> None:
        """Attach child; set parent linkage and call on_mount if already mounted."""
        if child.parent is not None:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)
        if self._mounted:
            child._mount()

    def remove_child(self, child: 'Component') -> None:
        """Detach child; call on_unmount if needed."""
        if child in self.children:
            self.children.remove(child)
            if child._mounted:
                child._unmount()
            child.parent = None

    def bring_to_front(self) -> None:
        """Move this component to end of parent's child list (top z-order)."""
        if self.parent and self in self.parent.children:
            self.parent.children.remove(self)
            self.parent.children.append(self)

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    def _mount(self) -> None:
        """Internal: propagate mount down tree."""
        if not self._mounted:
            self._mounted = True
            self.on_mount()
            for child in self.children:
                child._mount()

    def _unmount(self) -> None:
        """Internal: propagate unmount down tree."""
        if self._mounted:
            self._mounted = False
            self.on_unmount()
            for child in self.children:
                child._unmount()

    def on_mount(self) -> None:
        """Called once after added to a mounted parent (or App sets root as mounted)."""
        pass

    def on_unmount(self) -> None:
        """Called just before removal from tree."""
        pass

    # ─── Focus Management ────────────────────────────────────────────────────

    def on_focus(self) -> None:
        """Called when component receives focus."""
        self.focused = True

    def on_blur(self) -> None:
        """Called when component loses focus."""
        self.focused = False

    # ─── Frame Loop ──────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Update logic (e.g., animations, input state). Called every frame.
        Default: update children in order.
        """
        for child in self.children:
            child.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render self (and children) onto `surface`.
        Default: draws nothing — override in visual subclasses.
        Children drawn in order (first = back, last = front).
        """
        if not self.visible:
            return
        for child in self.children:
            child.draw(surface)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle Pygame event. Return True if consumed (stops propagation).
        Default: forward to children in reverse order (topmost first).
        Override to add interaction (e.g., click, drag).
        """
        if not self.enabled or not self.visible:
            return False

        # Event bubbling: children get first chance (reverse draw order = z-order)
        for child in reversed(self.children):
            if child.handle_event(event):
                return True
        return False

    # ─── Utilities ───────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        pos = (self.rect.x, self.rect.y)
        size = (self.rect.w, self.rect.h)
        status = 'visible' if self.visible else 'hidden'
        mounted = 'mounted' if self._mounted else 'unmounted'
        return f"<{cls} @ {pos} size={size} {status} {mounted}>"
import pygame
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from component import Component


class InputManager:
    """
    Centralized input handling for GUI framework.
    - Manages mouse & keyboard state (current + frame deltas)
    - Handles focus, capture, hover, and drag operations
    - Routes events to appropriate components
    """

    def __init__(self, debug: Callable[[str], None]):
        # Debug output callback
        self.write = debug

        # ─── Mouse State ─────────────────────────────────────────────────────
        self.mouse_pos = (0, 0)
        self.mouse_buttons = [False, False, False]              # L, M, R (held)
        self.mouse_buttons_pressed = [False, False, False]      # frame delta
        self.mouse_buttons_released = [False, False, False]     # frame delta

        # ─── Keyboard State ──────────────────────────────────────────────────
        self.keys = {}               # pygame.K_x → bool (held)
        self.keys_pressed = set()    # frame: newly pressed
        self.keys_released = set()   # frame: newly released

        # ─── Focus & Interaction ─────────────────────────────────────────────
        self.focused: Optional['Component'] = None      # receives keyboard input
        self.captured: Optional['Component'] = None     # captures mouse during drag
        self.hover_target: Optional['Component'] = None # component under cursor

        # ─── Drag State ──────────────────────────────────────────────────────
        self.drag_start_pos: Optional[tuple[int, int]] = None
        self.drag_offset: tuple[int, int] = (0, 0)

    def update(self, root: 'Component') -> None:
        """
        Call once per frame BEFORE processing events.
        Resets frame deltas and updates hover state.
        """
        # Reset frame-accurate deltas
        self.mouse_buttons_pressed = [False, False, False]
        self.mouse_buttons_released = [False, False, False]
        self.keys_pressed.clear()
        self.keys_released.clear()

        # Update hover in case visibility/position changed
        self._update_hover(root)

    def process_event(self, event: pygame.event.Event, root: 'Component') -> None:
        """Process a single pygame event and route to appropriate handler."""
        # Mouse motion
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self._handle_mouse_motion(root)

        # Mouse button down
        elif event.type == pygame.MOUSEBUTTONDOWN:
            btn_idx = self._button_to_index(event.button)
            if btn_idx is not None:
                self.mouse_buttons[btn_idx] = True
                self.mouse_buttons_pressed[btn_idx] = True
                self._handle_mouse_button_down(btn_idx, root)

        # Mouse button up
        elif event.type == pygame.MOUSEBUTTONUP:
            btn_idx = self._button_to_index(event.button)
            if btn_idx is not None:
                self.mouse_buttons[btn_idx] = False
                self.mouse_buttons_released[btn_idx] = True
                self._handle_mouse_button_up(btn_idx, root)

        # Keyboard down
        elif event.type == pygame.KEYDOWN:
            self.keys[event.key] = True
            self.keys_pressed.add(event.key)
            self._handle_key_down(event.key)

        # Keyboard up
        elif event.type == pygame.KEYUP:
            self.keys[event.key] = False
            self.keys_released.add(event.key)
            self._handle_key_up(event.key)

        # Window focus changes
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self._handle_app_focus(True)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self._handle_app_focus(False)

    # ─── Mouse Handlers ──────────────────────────────────────────────────────

    def _handle_mouse_motion(self, root: 'Component') -> None:
        """Handle mouse movement: update hover and propagate drag."""
        target = self._find_topmost_at(root, self.mouse_pos)

        # Hover enter/leave events
        if target != self.hover_target:
            if self.hover_target and hasattr(self.hover_target, 'on_mouse_leave'):
                self.hover_target.on_mouse_leave()
                self.hover_target.hovered = False

            self.hover_target = target

            if target and hasattr(target, 'on_mouse_enter'):
                target.on_mouse_enter()
                target.hovered = True

        # Propagate drag if captured
        if self.captured and self.drag_start_pos and hasattr(self.captured, 'on_drag'):
            dx = self.mouse_pos[0] - self.drag_start_pos[0]
            dy = self.mouse_pos[1] - self.drag_start_pos[1]
            self.captured.on_drag((dx, dy), self.drag_offset)

    def _handle_mouse_button_down(self, btn_idx: int, root: 'Component') -> None:
        """Handle mouse button press: focus, capture, and notify component."""
        target = self.hover_target or self._find_topmost_at(root, self.mouse_pos)

        if target:
            # Set focus if component is focusable
            if hasattr(target, 'focusable') and target.focusable:
                self.set_focus(target)

            # Notify component and check for capture
            if hasattr(target, 'on_mouse_down'):
                should_capture = target.on_mouse_down(btn_idx, self.mouse_pos)
                if should_capture:
                    self.captured = target
                    self.drag_start_pos = self.mouse_pos
                    local = target.global_to_local(self.mouse_pos)
                    self.drag_offset = local

            self.write(f'mouse_down({target.__class__.__name__} @ {target.rect.topleft})')

    def _handle_mouse_button_up(self, btn_idx: int, root: 'Component') -> None:
        """Handle mouse button release: click detection and capture release."""
        target = self.captured or self.hover_target or self._find_topmost_at(root, self.mouse_pos)

        if self.captured:
            # Notify captured component
            if hasattr(self.captured, 'on_mouse_up'):
                self.captured.on_mouse_up(btn_idx, self.mouse_pos)

            # Determine if this was a click or drag
            if self.drag_start_pos:
                dx = self.mouse_pos[0] - self.drag_start_pos[0]
                dy = self.mouse_pos[1] - self.drag_start_pos[1]
                dist_sq = dx * dx + dy * dy

                # Click threshold: 2px
                if dist_sq < 4 and hasattr(self.captured, 'on_click'):
                    self.captured.on_click(btn_idx, self.mouse_pos)

                # Always notify drag end if drag started
                if hasattr(self.captured, 'on_drag_end'):
                    self.captured.on_drag_end((dx, dy), self.drag_offset)

            self._release_capture()
            self.write(f'mouse_up(captured: {self.captured.__class__.__name__ if self.captured else None})')

        elif target:
            # Non-captured release (rare but possible)
            if hasattr(target, 'on_mouse_up'):
                target.on_mouse_up(btn_idx, self.mouse_pos)
            if hasattr(target, 'on_click'):
                target.on_click(btn_idx, self.mouse_pos)
            self.write(f'mouse_up({target.__class__.__name__})')

    # ─── Keyboard Handlers ───────────────────────────────────────────────────

    def _handle_key_down(self, key: int) -> None:
        """Route key press to focused component."""
        if self.focused and hasattr(self.focused, 'on_key_down'):
            self.focused.on_key_down(key)
        self.write(f'key_down({pygame.key.name(key)})')

    def _handle_key_up(self, key: int) -> None:
        """Route key release to focused component."""
        if self.focused and hasattr(self.focused, 'on_key_up'):
            self.focused.on_key_up(key)
        self.write(f'key_up({pygame.key.name(key)})')

    # ─── Focus Management ────────────────────────────────────────────────────

    def set_focus(self, component: Optional['Component']) -> None:
        """Set keyboard focus to component (or None to clear)."""
        if self.focused is component:
            return

        # Blur previous
        if self.focused:
            if hasattr(self.focused, 'on_blur'):
                self.focused.on_blur()
            self.focused.focused = False

        # Focus new
        self.focused = component
        if self.focused:
            if hasattr(self.focused, 'on_focus'):
                self.focused.on_focus()
            self.focused.focused = True

    def _handle_app_focus(self, gained: bool) -> None:
        """Handle window focus changes."""
        if not gained:
            # Clear all input state when window loses focus
            self.mouse_buttons = [False, False, False]
            self.keys.clear()
            if self.focused and hasattr(self.focused, 'on_blur'):
                self.focused.on_blur()
                self.focused.focused = False

    # ─── Capture Management ──────────────────────────────────────────────────

    def _release_capture(self) -> None:
        """Release mouse capture and reset drag state."""
        if self.captured:
            self.captured.dragging = False
            self.captured = None
        self.drag_start_pos = None
        self.drag_offset = (0, 0)

    # ─── Hit Testing ─────────────────────────────────────────────────────────

    def _find_topmost_at(self, root: 'Component', global_pos: tuple[int, int]) -> Optional['Component']:
        """
        Find topmost visible & enabled component at global_pos.
        Uses DFS with reverse child order (respects draw/z-order).
        """
        def _dfs(node: 'Component') -> Optional['Component']:
            if not node.visible or not node.enabled:
                return None

            # Check children first (reverse = top-down z-order)
            for child in reversed(node.children):
                if child.contains_global(global_pos):
                    deeper = _dfs(child)
                    if deeper:
                        return deeper

            # If no child claims it and node contains point → return node
            if node.contains_global(global_pos):
                return node

            return None

        return _dfs(root)

    def _update_hover(self, root: 'Component') -> None:
        """Recompute hover target (useful after visibility/layout changes)."""
        new_target = self._find_topmost_at(root, self.mouse_pos)
        if new_target != self.hover_target:
            if self.hover_target and hasattr(self.hover_target, 'on_mouse_leave'):
                self.hover_target.on_mouse_leave()
                self.hover_target.hovered = False
            self.hover_target = new_target
            if new_target and hasattr(new_target, 'on_mouse_enter'):
                new_target.on_mouse_enter()
                new_target.hovered = True

    # ─── Utilities ───────────────────────────────────────────────────────────

    def _button_to_index(self, button: int) -> Optional[int]:
        """Map pygame button ID to index (0=L, 1=M, 2=R). Ignores scroll."""
        if button == 1:
            return 0  # Left
        elif button == 3:
            return 2  # Right
        elif button == 2:
            return 1  # Middle
        return None  # Ignore scroll wheel (4, 5)

    def is_mouse_down(self, button: int = 0) -> bool:
        """Check if mouse button is held (0=L, 1=M, 2=R)."""
        return 0 <= button < 3 and self.mouse_buttons[button]

    def is_key_down(self, key: int) -> bool:
        """Check if keyboard key is held."""
        return self.keys.get(key, False)
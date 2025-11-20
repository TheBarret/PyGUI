import pygame
from typing import Optional, Literal
from component import Component
from console import Console

Workflow = Literal['normal', 'modal', 'fullscreen']


class Shell(Component):
    """
    Root container component for the GUI framework.
    - Acts as the symbolic root where all other components are attached
    - Supports workflow modes: normal, modal, fullscreen
    - Includes integrated debug console
    """

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        w: int = 400,
        h: int = 300,
        *,
        title: str = "",
        resizable: bool = True
    ):
        super().__init__(x, y, w, h)
        self.title = title
        self.resizable = resizable

        # ─── Workflow State ──────────────────────────────────────────────────
        self._workflow: Workflow = 'normal'
        self._previous_rect = self.rect.copy()  # restore after modal/fullscreen

        # ─── Debug Console ───────────────────────────────────────────────────
        self.debugger = Console(x=0, y=500, w=800, h=100)
        self.add_child(self.debugger)
        self.write('Shell initialized')

    # ─── Properties ──────────────────────────────────────────────────────────

    @property
    def workflow(self) -> Workflow:
        """Current workflow mode: 'normal', 'modal', or 'fullscreen'."""
        return self._workflow

    # ─── Debug Logging ───────────────────────────────────────────────────────

    def write(self, entry: str) -> None:
        """Write message to debug console."""
        if self.debugger:
            self.debugger.log(entry)

    # ─── Workflow Management ─────────────────────────────────────────────────

    def set_modal(self, modal: bool = True) -> None:
        """
        Toggle modal mode.
        In modal mode, the shell is brought to front and should capture input focus.
        InputManager should handle modal behavior by checking workflow state.
        """
        if modal == (self._workflow == 'modal'):
            return  # Already in desired state

        if modal:
            # Save state before going modal
            self._previous_rect = self.rect.copy()
            self._workflow = 'modal'
            self.bring_to_front()
            self.write(f'Modal enabled: {self.title or self.__class__.__name__}')
        else:
            # Restore state
            self._workflow = 'normal'
            self.rect = self._previous_rect.copy()
            self.write(f'Modal disabled: {self.title or self.__class__.__name__}')

    def set_fullscreen(self, fullscreen: bool = True) -> None:
        """
        Toggle fullscreen mode.
        Notifies root via _on_fullscreen callback if available.
        Root should handle actual window fullscreen state.
        """
        if fullscreen == (self._workflow == 'fullscreen'):
            return  # Already in desired state

        root = self._find_root()
        if not root:
            raise RuntimeError("Shell not attached to root - cannot go fullscreen")

        if fullscreen:
            # Save state before going fullscreen
            self._previous_rect = self.rect.copy()
            self._workflow = 'fullscreen'

            # Notify root to handle window-level fullscreen
            if hasattr(root, '_on_fullscreen'):
                root._on_fullscreen(self, True)
            self.write(f'Fullscreen enabled: {self.title or self.__class__.__name__}')
        else:
            # Restore state
            self._workflow = 'normal'
            self.rect = self._previous_rect.copy()

            # Notify root to exit fullscreen
            if hasattr(root, '_on_fullscreen'):
                root._on_fullscreen(self, False)
            self.write(f'Fullscreen disabled: {self.title or self.__class__.__name__}')

    def close(self) -> None:
        """Remove this shell from parent (closes the window)."""
        if self.parent:
            self.parent.remove_child(self)
            self.write(f'Shell closed: {self.title or self.__class__.__name__}')

    # ─── Utilities ───────────────────────────────────────────────────────────

    def _find_root(self) -> Optional[Component]:
        """Walk up parent chain to find root component."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node
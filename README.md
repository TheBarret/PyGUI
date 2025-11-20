# PyGUI
Tiny PyGame GUI Framework (WIP)

### Foundation
- Core Foundation (component.py): Hierarchical atom component system
- Application Layer (main.py): Game loop and lifecycle management
- Container System (shell.py): Window/workflow management
- Input Pipeline (ioman.py): Sophisticated event routing
- Widget Library (widgets.py): Reusable UI tiered components
- Styling System (theme.py): Consistent visual design
    
### Main application class - handles window, event loop, and subsystems.
- Fixed timestep updates (tick_rate) with variable rendering
- Centralized input management via InputManager
- Component tree lifecycle management

### Per Frame
1. Measure time delta (dt)
2. Accumulate dt
3. Process input (once per frame)
4. Update input manager deltas (once per frame)
5. While accumulated >= tick_rate:
   - Update game state with fixed tick_rate
   - Subtract tick_rate from accumulator
6. Render current state (interpolation optional)
7. Limit FPS

### Example

Setup:
```py
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
```
<img width="802" height="632" alt="image" src="https://github.com/user-attachments/assets/7d5d92b3-d15b-4c6d-b18c-114514c142a3" />

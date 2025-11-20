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

<img width="802" height="632" alt="image" src="https://github.com/user-attachments/assets/7d5d92b3-d15b-4c6d-b18c-114514c142a3" />

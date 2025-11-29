from core import Engine
from primitives import Gui


# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'init')
    
    for i in range(0, 4):
        dialog1 = (Gui(init)
              .create(i*10, i*10, 350, 220)
              .as_dialog(f'Message Box {i}', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')
              .build())
    
    init.set_theme()
    
    init.run()
    
    
    

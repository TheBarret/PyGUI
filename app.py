from core import Engine
from primitives import Gui


# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'init')
    
    dialog = (Gui(init)
              .create(200, 100, 250, 120)
              .as_dialog('Window')
              .set_theme()
              .build())
    
   
    init.run()
    
    
    

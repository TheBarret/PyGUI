from core import Engine
from builders import Gui


# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'init')
    
    window = (Gui(init)
              .create(200, 170, 350, 200)
              .as_window(f'Config')
              .with_toolbar(4)
              .add_control()
              .finalize()
              .build())    
        
    # set base theme
    init.set_theme(225)
    
    # run
    init.run()
    
    
    

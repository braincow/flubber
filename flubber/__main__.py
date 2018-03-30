try:
    from flubber import gui
except ImportError:
    from . import gui

gui.main()

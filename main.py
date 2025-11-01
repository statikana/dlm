# import threading
# from interface.progress_window import ProgressWindow
# from src.dlm.dlm import DLM


# dlm = DLM(n_threads=4)
# url= "\
# https://plus.unsplash.com/premium_photo-1750672581729-a6da4cb5a0eb?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1160\
# "
# target = "downloads/img.jpeg"

# dlm.prepare_modules(url, target)

# window = ProgressWindow(dlm.modules)

# dlm.start(target)
# window.display()  # tkinter takes over the main thread

from src.interface.gui import Gui

Gui().root.mainloop()

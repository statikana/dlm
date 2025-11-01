import threading
from tkinter import Tk
from tkinter import ttk
from ..dlm.dlm import DownloadModule


class ProgressWindow:
    def __init__(self, modules: list[DownloadModule]):
        self.modules = modules
        self.progress_components: list[ttk.Progressbar] = []
        self.root = Tk()
        self.frame = ttk.Frame(self.root, padding=20)

        self.frame.pack(fill="both", expand=True)
        self.root.title("Progress")

        for n, m in enumerate(self.modules):
            row = n
            col = 1

            ttk.Label(self.frame, text=m.thread.name).grid(column=col, row=row)
            bar = ttk.Progressbar(self.frame, length=100, orient="horizontal")

            bar.grid(column=col + 1, row=row)
            self.progress_components.append(bar)

        self.root.after(100, self.update_ui)

    def display(self) -> None:
        self.root.mainloop()

    def update_ui(self) -> None:
        remaining = False
        for n, bar in enumerate(self.progress_components):
            p = self.modules[n].tracker.p
            if p <= 0.99:
                remaining = True
            bar["value"] = p * 100

        if remaining:
            self.root.after(100, self.update_ui)

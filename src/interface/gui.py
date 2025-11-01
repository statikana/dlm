import os
import re
from tkinter import NORMAL, Tk, StringVar, IntVar, DISABLED
from tkinter.messagebox import Message
from tkinter import ttk

from ..dlm.dlm import DLM, DownloadModule
from ..dlm.progress_tracker import ProgressTracker


RE_URL = re.compile(
    r"/^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/"
)


def fmt_size(size: int) -> str:
    suffixes = ["bytes", "KB", "MB", "GB"]
    for s in suffixes:
        if size < 1000:
            return f"{size}{s}"
        size = round(size / 1000)

    return f"{size}PB"


class Gui:
    def __init__(self) -> None:
        self.target_file: str | None = None
        self.dlm: DLM | None = None
        self.tracker_components: list[tuple[ttk.Progressbar, ttk.Label]] = []
        self.start_button: ttk.Button | None = None

        self.root = Tk()
        for n in range(4):
            self.root.columnconfigure(n, weight=1)

        self.root.title("Progress")

        # required fields to download
        self.url_entry: ttk.Entry | None = None
        self.n_threads_entry: ttk.Entry | None = None

        # bars to keep track of
        self.progress_comps: list[ttk.Progressbar] = []

        # other things / settings
        # let the user set custom cookies etc. in .session?

        self.build()

    def build(self) -> None:
        top = self.build_top_frame()
        top.pack(side="top")

        bottom = self.build_bottom_frame()
        bottom.pack(side="bottom")

    def build_top_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="top")

        def url_paste_cmd() -> None:
            if self.url_entry is None:
                return
            self.url_entry.selection_clear()
            self.url_entry.insert(0, self.root.clipboard_get())

        label = ttk.Label(frame, text="URL to download:")
        label.grid(row=0, column=0, columnspan=1, sticky="w")

        entry = self.url_entry = ttk.Entry(frame, width=50)
        entry.grid(row=1, column=0, columnspan=5)

        paste = ttk.Button(frame, text="Paste", command=url_paste_cmd)
        paste.grid(row=0, column=4, sticky="e")

        sep = ttk.Separator(frame, orient="vertical")
        sep.grid(row=0, rowspan=2, column=5, sticky="ns", padx=7)

        label = ttk.Label(frame, text="# Concurrent Threads:")
        label.grid(row=0, column=6, sticky="w")

        entry = self.n_threads_entry = ttk.Entry(frame)
        entry.grid(row=1, column=6, columnspan=2, sticky="w")
        entry.insert(0, str(10))

        sep = ttk.Separator(frame, orient="horizontal")
        sep.grid(row=2, column=0, columnspan=7, sticky="ew", pady=10)

        return frame

    def build_bottom_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="bottom")

        sep = ttk.Separator(frame, orient="horizontal")
        sep.grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)

        init_button = ttk.Button(frame, text="Init", command=self.init)
        init_button.grid(row=1, column=0, sticky="w")

        start_button = self.start_button = ttk.Button(
            frame, text="Start", command=self.start
        )
        start_button.config(state=DISABLED)
        start_button.grid(row=1, column=1)

        other_settings_button = ttk.Button(frame, text="Settings..")
        other_settings_button.grid(row=1, column=2, sticky="e")

        return frame

    def build_tracker_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="tracker")
        self.tracker_components.clear()

        if self.dlm is None:
            return frame

        for n, m in enumerate(self.dlm.modules):
            thread_label = ttk.Label(frame, text=m.thread.name)
            thread_label.grid(row=n, column=0, sticky="w")

            bar = ttk.Progressbar(frame, maximum=1, mode="determinate", length=300)
            bar.grid(row=n, column=1, sticky="ew")

            size_label = ttk.Label(frame, text=self.fmt_progress_label(m.tracker))
            size_label.grid(row=n, column=2, sticky="e")

            self.tracker_components.append((bar, size_label))
        return frame

    def init(self) -> None:
        """Start internal dlm and adjust windows"""
        if self.url_entry is None or self.n_threads_entry is None:
            return

        url = self.url_entry.get()
        # if not RE_URL.fullmatch(self.url_entry.get()):
        #     Message(message="Invalid URL.").show()
        #     return

        n_threads_str = self.n_threads_entry.get()
        if not self.n_threads_entry.get().isdigit():
            Message(message="Invalid number of threads. Please choose a number.")
        n_threads = int(n_threads_str)

        self.dlm = DLM(
            n_threads=n_threads,
            request_session=None,
            writing_chunk_size_bytes=50,  # for testing
        )

        self.dlm.prepare_modules(url, target_file="./downloads/idk.png")

        tracker_frame = self.build_tracker_frame()
        tracker_frame.pack(anchor="center")

        if self.start_button is None:
            return
        self.start_button.config(state=NORMAL)

    def start(self) -> None:
        if self.dlm is None:
            return

        self.dlm.start("./downloads/idk.png")
        self.update_progress_bars(100)

    def fmt_progress_label(self, t: ProgressTracker) -> str:
        return f"{fmt_size(t.current-t.start)}/{fmt_size(t.end-t.start)} [{round(t.p*100, 2)}%]"

    def update_progress_bars(self, ms: int) -> None:
        if self.dlm is None:
            return

        for n, (bar, label) in enumerate(self.tracker_components):
            t = self.dlm.modules[n].tracker
            bar["value"] = t.p
            label["text"] = self.fmt_progress_label(t)

        if all(m.tracker.done for m in self.dlm.modules):
            name = self.dlm.modules[0].file.name # type: ignore
            Message(message=f"Finished downloading. Saved to {name}").show()
            return
        else:
            print("not done")

        self.root.after(ms, self.update_progress_bars, ms)

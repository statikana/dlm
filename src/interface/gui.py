"""Tkinter UI for the DLM download manager."""

import re
from tkinter import DISABLED, NORMAL, Tk, ttk
from tkinter.messagebox import Message

from ..dlm.dlm import DLM
from ..dlm.progress_tracker import ProgressTracker


RE_URL = re.compile(
    r"/^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/"
)


def fmt_size(size: int) -> str:
    """Format a byte count into a compact human-readable value."""
    suffixes = ["bytes", "KB", "MB", "GB"]
    for suffix in suffixes:
        if size < 1000:
            return f"{size}{suffix}"
        size = round(size / 1000)
    return f"{size}PB"


class Gui:
    """Simple UI for preparing and starting a multi-threaded download."""

    def __init__(self) -> None:
        self.target_file: str | None = None
        self.dlm: DLM | None = None
        self.tracker_components: list[tuple[ttk.Progressbar, ttk.Label]] = []
        self.start_button: ttk.Button | None = None

        self.root = Tk()
        for n in range(4):
            self.root.columnconfigure(n, weight=1)

        self.root.title("Progress")
        self.url_entry: ttk.Entry | None = None
        self.n_threads_entry: ttk.Entry | None = None

        self.build()

    def build(self) -> None:
        """Create and place the top and bottom UI sections."""
        self.build_top_frame().pack(side="top")
        self.build_bottom_frame().pack(side="bottom")

    def build_top_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="top")

        def paste_url() -> None:
            if self.url_entry is None:
                return
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, self.root.clipboard_get())

        ttk.Label(frame, text="URL to download:").grid(row=0, column=0, sticky="w")

        self.url_entry = ttk.Entry(frame, width=50)
        self.url_entry.grid(row=1, column=0, columnspan=5)

        ttk.Button(frame, text="Paste", command=paste_url).grid(
            row=0, column=4, sticky="e"
        )
        ttk.Separator(frame, orient="vertical").grid(
            row=0, rowspan=2, column=5, sticky="ns", padx=7
        )

        ttk.Label(frame, text="# Concurrent Threads:").grid(
            row=0, column=6, sticky="w"
        )
        self.n_threads_entry = ttk.Entry(frame)
        self.n_threads_entry.grid(row=1, column=6, columnspan=2, sticky="w")
        self.n_threads_entry.insert(0, "10")

        ttk.Separator(frame, orient="horizontal").grid(
            row=2, column=0, columnspan=7, sticky="ew", pady=10
        )
        return frame

    def build_bottom_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="bottom")

        ttk.Separator(frame, orient="horizontal").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=10
        )
        ttk.Button(frame, text="Init", command=self.init).grid(
            row=1, column=0, sticky="w"
        )

        self.start_button = ttk.Button(frame, text="Start", command=self.start)
        self.start_button.config(state=DISABLED)
        self.start_button.grid(row=1, column=1)

        # Settings are not implemented yet; keep the button visible as a placeholder.
        ttk.Button(frame, text="Settings..").grid(row=1, column=2, sticky="e")
        return frame

    def build_tracker_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.root, name="tracker")
        self.tracker_components.clear()

        if self.dlm is None:
            return frame

        for n, module in enumerate(self.dlm.modules):
            ttk.Label(frame, text=module.thread.name).grid(
                row=n, column=0, sticky="w"
            )
            bar = ttk.Progressbar(frame, maximum=1, mode="determinate", length=300)
            bar.grid(row=n, column=1, sticky="ew")

            size_label = ttk.Label(frame, text=self.fmt_progress_label(module.tracker))
            size_label.grid(row=n, column=2, sticky="e")
            self.tracker_components.append((bar, size_label))

        return frame

    def init(self) -> None:
        """Prepare a download and set up its progress bars."""
        if self.url_entry is None or self.n_threads_entry is None:
            return

        url = self.url_entry.get().strip()
        n_threads_str = self.n_threads_entry.get().strip()
        if not n_threads_str.isdigit() or int(n_threads_str) < 1:
            Message(message="Enter a positive number of threads.").show()
            return

        self.dlm = DLM(n_threads=int(n_threads_str))
        try:
            self.target_file = self.dlm.prepare_modules(
                url, target_file="./downloads/idk.png"
            )
        except (requests.RequestException, KeyError, ValueError, RuntimeError) as error:
            Message(message=f"Could not prepare download: {error}").show()
            self.dlm = None
            return

        tracker_frame = self.build_tracker_frame()
        tracker_frame.pack(anchor="center")

        if self.start_button is not None:
            self.start_button.config(state=NORMAL)

    def start(self) -> None:
        """Start the prepared download and update progress in the UI."""
        if self.dlm is None or self.target_file is None:
            return

        try:
            self.dlm.start(self.target_file)
        except OSError as error:
            Message(message=f"Could not start download: {error}").show()
            return
        self.update_progress_bars(100)

    def fmt_progress_label(self, tracker: ProgressTracker) -> str:
        """Return a compact label such as '10MB/20MB [50%]'."""
        return (
            f"{fmt_size(tracker.current - tracker.start)}/"
            f"{fmt_size(tracker.end - tracker.start)} "
            f"[{round(tracker.p * 100, 2)}%]"
        )

    def update_progress_bars(self, ms: int) -> None:
        """Refresh progress bars and stop polling once every range is complete."""
        if self.dlm is None:
            return

        for n, (bar, label) in enumerate(self.tracker_components):
            tracker = self.dlm.modules[n].tracker
            bar["value"] = tracker.p
            label["text"] = self.fmt_progress_label(tracker)

        if all(module.tracker.done for module in self.dlm.modules):
            Message(message=f"Finished downloading. Saved to {self.target_file}").show()
            return

        self.root.after(ms, self.update_progress_bars, ms)

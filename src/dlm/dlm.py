"""Core multi-threaded download logic."""

import io
import logging
import os
import threading
import time
from typing import Generator

import requests

from .progress_tracker import ProgressTracker


class DLM:
    """Download a file by splitting it into byte ranges and fetching them in parallel."""

    def __init__(
        self,
        *,
        n_threads: int,
        request_session: requests.Session | None = None,
        writing_chunk_size_bytes: int = 50,
    ) -> None:
        self.n_threads = n_threads
        self.session = request_session or requests.Session()
        self.chunk_size = writing_chunk_size_bytes
        self.stop_flag = threading.Event()
        self._lock = threading.Lock()
        self.modules: list[DownloadModule] = []

    def download(self, url: str, target_file: str | None = None) -> None:
        """Prepare and start a download, stopping workers on keyboard interrupt."""
        try:
            target_file = self.prepare_modules(url, target_file)
            self.start(target_file)
        except KeyboardInterrupt:
            self.stop_flag.set()
            print("exit")

    def prepare_modules(self, url: str, target_file: str | None) -> str:
        """Create one download worker per byte range and return the target path."""
        self.modules.clear()

        with self.session.request("HEAD", url, timeout=10) as response:
            headers = response.headers
            supported = headers.get("Accept-Ranges")
            if supported is None or "bytes" not in supported.split(", "):
                logging.fatal(
                    "Host does not support chunking, defaulting to single-threaded."
                )
                raise RuntimeError("Remote host does not support byte ranges")

            filetype = headers["Content-Type"].split("/")[1]

        if target_file is not None and not target_file.endswith(filetype):
            logging.warning("Target and download file extensions do not match.")

        if target_file is None:
            target_file = f"./downloads/download_{round(time.time())}.{filetype}"

        size = int(headers["Content-Length"])
        ranges = list(self.get_ranges(size))

        print(f"File size: {size}")
        print(f"Target file: {target_file}")

        for n, (start, end) in enumerate(ranges):
            print(
                f"\r{n + 1}/{self.n_threads} modules created "
                f"[bytes {start}-{end} ({round(end / size * 100)}%)]",
                end="",
            )

            module = DownloadModule(
                lock=self._lock,
                stop_flag=self.stop_flag,
                chunk_size=self.chunk_size,
                url=url,
                session=self.session,
                range=(start, end),
            )
            module.thread.name = f"T{n}"
            self.modules.append(module)

        print()
        return target_file

    def start(self, target_file: str) -> None:
        """Create the destination file and launch each worker thread."""
        directory = os.path.dirname(target_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        try:
            with open(target_file, "x"):
                pass
        except FileExistsError:
            with open(target_file, "w"):
                pass

        file = open(target_file, "r+b")
        for module in self.modules:
            module.begin(file)

    def get_ranges(self, size: int) -> Generator[tuple[int, int]]:
        """Split a file size into balanced byte ranges for each thread."""
        difference = size % self.n_threads
        effective_size = size + (self.n_threads - difference)

        chunk_size = effective_size // self.n_threads
        current = 0
        while current < size:
            yield current, current + chunk_size
            current += chunk_size


class DownloadModule:
    """One worker that downloads a specific byte range from the server."""

    def __init__(
        self,
        *,
        session: requests.Session,
        url: str,
        chunk_size: int,
        range: tuple[int, int],
        lock: threading.Lock,
        stop_flag: threading.Event,
    ) -> None:
        self.file_lock = lock
        self.stop_flag = stop_flag
        self.chunk_size = chunk_size
        self.url = url
        self.session = session
        self.range = range

        self.tracker: ProgressTracker = ProgressTracker(*self.range)
        self.file: io.BufferedRandom | None = None
        self.thread = threading.Thread(target=self._download)

    def begin(self, file: io.BufferedRandom):
        """Attach the output file and start the worker thread."""
        self.file = file
        self.thread.start()

    def _download(self) -> None:
        """Read the target range in chunks and write it to the file."""
        if self.file is None:
            raise RuntimeError("DownloadModule.target_file not set")

        headers = {"Range": f"bytes={self.range[0]}-{self.range[1] - 1}"}
        with self.session.get(self.url, headers=headers, stream=True, timeout=10) as response:
            seek_pos = self.range[0]

            for chunk in response.iter_content(self.chunk_size, decode_unicode=False):
                if self.stop_flag.is_set():
                    break

                with self.file_lock:
                    self.file.seek(seek_pos)
                    self.file.write(chunk)

                seek_pos += len(chunk)
                self.tracker.update(seek_pos)

import io
import logging
import os
import pprint
import threading
from typing import Generator
import requests
import time


class IDM:
    def __init__(
        self,
        *,
        n_threads: int,
        request_session: requests.Session | None = None,
        writing_chunk_size_bytes: int = 500_000, # 5 MB per write
    ) -> None:
        self.n_threads = n_threads
        self.session = request_session or requests.Session()
        self.chunk_size = writing_chunk_size_bytes
    
    def download(self, url: str, target_file: str | None = None):
        with self.session.request("HEAD", url) as r:
        
            headers = r.headers
            supported = headers.get("Accept-Ranges", None)
            if supported is None or "bytes" not in supported.split(", "):
                logging.fatal("Host does not support chunking, defaulting to single-threaded.")
                exit()

            pprint.pprint(headers)
            filetype = headers["Content-Type"].split("/")[1]

        if target_file is not None and not target_file.endswith(filetype):
            logging.warning("Target and download file extensions do not match.")

        if target_file is None:
            target_file = f"download_{round(time.time())}.{filetype}"
        
        size = int(headers["Content-Length"])
        ranges = list(self.get_ranges(size))

        
        self.prep_file(target_file)

        lock = threading.Lock()
        

        file = open(target_file, "r+b") # no context manager!

        print(f"File size: {size}")
        print(f"Target file: {target_file}")

        for n, (a, b) in enumerate(ranges):
            print(f"\r{n+1}/{self.n_threads} threads dispatched [bytes 0-{b}]", end="")
            module = DownloadModule(
                lock=lock,
                chunk_size=self.chunk_size,
                url=url,
                session=self.session,
                range=(a, b)
            )
            t = threading.Thread(
                    target=module.begin,
                    args=[file]
                )
            t.start()


    def get_ranges(
        self,
        size: int
    ) -> Generator[tuple[int, int]]:
        difference = size % self.n_threads
        effective_size = size + (self.n_threads - difference)

        chunk_size = effective_size // self.n_threads
        current = 0
        while current < size:
            yield current, current + chunk_size
            current += chunk_size
    
    def prep_file(self, target_file: str):
        try:
            open(target_file, "x")
        except FileExistsError:
            logging.warning(f"'{target_file} already exists, content will be overwritten.")


class DownloadModule:
    def __init__(
        self,
        lock: threading.Lock,
        chunk_size: int,
        url: str,
        session: requests.Session,
        range: tuple[int, int],
    ) -> None:
        self.lock = lock
        self.chunk_size = chunk_size
        self.url = url
        self.session = session
        self.range = range

    
    def begin(self, file: io.BufferedRandom) -> None:
        """Starts a download stream in chunks."""
        headers = {
            "Range": f"bytes={self.range[0]}-{self.range[1]-1}"
        }
        with self.session.get(
            self.url,
            headers=headers,
            stream=True
        ) as r:
            seek_pos = self.range[0]

            for chunk in r.iter_content(self.chunk_size, decode_unicode=False):
                with self.lock:
                    file.seek(seek_pos)
                    file.write(chunk)
                
                seek_pos += self.chunk_size

url = "\
http://ipv4.download.thinkbroadband.com/5GB.zip\
"
idm = IDM(n_threads=10)

idm.download(url, "mything.zip")

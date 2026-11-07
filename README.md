# DLM

DLM is a small Python download manager that splits a file into ranges and downloads them concurrently. It includes a Tkinter interface for entering a URL and starting the transfer.

## What it does

- Downloads a file from a URL using multiple threads.
- Uses HTTP range requests to divide the file into chunks.
- Tracks download progress per worker.
- Starts from a simple GUI in `main.py`.

## Project layout

- `main.py` launches the app.
- `src/dlm/dlm.py` contains the downloader logic.
- `src/dlm/progress_tracker.py` tracks per-range progress.
- `src/interface/gui.py` implements the Tkinter UI.

## Run it

```bash
python main.py
```

Then paste a URL into the app, choose the number of threads, and start the download.

## Notes

This is a lightweight experimental project rather than a production-grade downloader. It is useful for learning chunked downloading and basic GUI integration.

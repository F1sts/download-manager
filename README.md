# **Multi-Threaded Download Manager**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A fast, reliable, multi-threaded file downloader with resume support, progress bars, and download history logging. Built with Python, [`requests`](https://pypi.org/project/requests/) and [`rich`](https://pypi.org/project/rich/).

---

## 🚀 Features

- **Multi-threaded downloads**: Split files into chunks and download in parallel for maximum speed.
- **Automatic fallback**: Detects when the server doesn’t support byte ranges and falls back to single-threaded mode.
- **Resume & caching**: Partial chunks are stored in `./cache/` and cleaned up on failure or merged on success.
- **Rich progress display**: Real-time per-thread and overall progress bars, transfer speeds, and time remaining.
- **Logging**: All completed downloads are logged with timestamps in `download_history.log`.
- **Filename sanitization**: Safe and clean filenames are generated from URLs or `Content-Disposition` headers.
- **Cross-platform**: Works on Windows, macOS, and Linux.

## 📦 Prerequisites

- Python **3.8** or higher

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/F1sts/download-manager.git
   cd download-manager
   ```

2. **Create & activate a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/macOS
   venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Constants in the script can be customized at the top of the file:

| Constant                | Default        | Description                                        |
| ----------------------- | -------------- | -------------------------------------------------- |
| `CACHE_DIR`             | `./cache/`     | Directory to store partial chunk files.            |
| `DOWNLOAD_DIR`          | `./downloads/` | Directory to save final merged downloads.          |
| `REQUEST_TIMEOUT`       | `60`           | Timeout (in seconds) for HTTP GET requests.        |
| `CHUNK_ITER_SIZE`       | `8192`         | Number of bytes per chunk write iteration.         |
| `HEAD_REQUEST_TIMEOUT`  | `10`           | Timeout (in seconds) for HTTP HEAD requests.       |

## 🎉 Usage

Run the downloader script directly:

```bash
py main.py
```

1. **Enter the file URL** when prompted.
2. **Choose number of threads** or leave empty for auto-selection.
3. **Watch the rich progress bars** as chunks download in parallel.
4. **Find your file** in the `downloads/` folder once complete.

### Example

```text
🔗 | Enter the URL of the file you want to download: https://example.com/largefile.zip
💪 | How many threads would you like to use? (Empty means 'Let program decide'): 8
⏳ | Downloading 'largefile.zip' (150.23 MB) using 8 threads...
…(progress bars)…
✔️ | File 'largefile.zip' merged successfully!
😎 | Saved as 'largefile.zip' in the 'downloads' folder.
```  

## 📂 Folder Structure

```
├── cache/                # Temporary chunk storage
├── downloads/            # Final downloaded files
├── download_history.log  # Log of past downloads
├── main.py               # Main script
└── requirements.txt      # Python dependencies
```

## 📝 Logging

Every successful download is recorded in `download_history.log` with a timestamp and final filename:

```text
[Saturday, 26 April 2025 - 14:32 (02:32 PM)] → https://example.com/largefile.zip >> largefile.zip
```

## 💡 Tips & Troubleshooting

- If the download fails or server doesn’t support multi-threading, the script falls back to a single thread.
- Ensure you have write permissions for the `cache/` and `downloads/` directories.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Please:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature-name`)
5. Open a Pull Request

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

*Built by Fists & Rist.*
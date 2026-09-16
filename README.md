# 🎬 Studio Downloader

A modern, fast, and feature-rich desktop media downloader built with **Python** and **PyQt5**. Studio Downloader allows you to fetch, queue, and download high-quality videos and audio tracks from **YouTube** and **TikTok** with real-time progress tracking.

---

## ✨ Features

- ⚡ **Multi-Platform Support:** Seamlessly download videos and audio from both **YouTube** and **TikTok**.
- 📋 **Batch & Queue Management:** Add single links or entire YouTube playlists to a download queue; process them sequentially.
- 🎵 **Audio & Video Extraction:** Choose between full video downloads or extract audio as high-bitrate MP3 (up to 320 kbps).
- 🎯 **Quality Selection:** Download in multiple resolutions (1080p, 720p, 480p, 360p) or highest available quality.
- 🧵 **Asynchronous Architecture:** UI stays completely responsive during network calls and downloads using QThread.
- ⏸️ **Pause / Resume / Cancel:** Full control over active download tasks with dedicated threading events.
- 🖼️ **Live Metadata Preview:** Automatic fetching of video titles, channel names, duration, and high-res thumbnails.
- 📜 **Download History:** Dedicated history tab tracking completed and failed downloads with timestamps.
- 🌓 **Dark & Light Modes:** Sleek dashboard with custom QSS styling and one-click theme toggle.
- 🌐 **Bilingual Interface:** Instant language switching between English and Turkish.

---

## 🛠️ Tech Stack

- **GUI Framework:** PyQt5
- **Media Engine:** yt-dlp
- **Audio/Video Processing:** static-ffmpeg
- **Concurrency:** Python threading & QThread

---

## 🚀 Installation

### 1. Clone the repository
git clone [https://github.com/AtmacaYigit/studio-downloader.git](https://github.com/AtmacaYigit/studio-downloader.git)
cd studio-downloader

### 2. Install dependencies
pip install PyQt5 yt-dlp static-ffmpeg

### 3. Run the application
python yt_converter.py

---

## 📖 How to Use

1. **Paste Link:** Enter a YouTube or TikTok link into the input bar.
2. **Preview:** The application automatically displays title, creator, and thumbnail.
3. **Configure:** Choose Video or Audio, select desired resolution/bitrate, and pick a destination folder.
4. **Queue & Download:** Click "Add to Queue" (or queue an entire playlist), then hit "Start Download".

---

## 📂 Project Structure

```text
studio-downloader/
│
├── yt_converter.py
├── requirements.txt
├── .gitignore
└── README.md

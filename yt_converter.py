import sys
import os
import platform
import subprocess
import threading
import urllib.request
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QComboBox,
    QProgressBar, QLabel, QMessageBox, QFileDialog, QFrame,
    QListWidget, QListWidgetItem, QStackedWidget, QButtonGroup,
    QGraphicsDropShadowEffect, QTabWidget
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QColor
import yt_dlp

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCENT_A = "#6366f1"
ACCENT_B = "#8b5cf6"

# ---------------------------------------------------------------------------
# Çeviriler
# ---------------------------------------------------------------------------
STRINGS = {
    "tr": {
        "window_title": "Studio Downloader",
        "app_title": "Studio Downloader",
        "app_subtitle": "Videoları ve şarkıları saniyeler içinde indir",
        "url_placeholder": "Bir YouTube video ya da liste bağlantısı yapıştırın…",
        "paste": "Yapıştır",
        "add_queue": "Kuyruğa Ekle",
        "preview_title_empty": "Henüz bir bağlantı yok",
        "preview_subtitle_empty": "Başlamak için yukarıya bir video ya da oynatma listesi linki yapıştırın",
        "preview_fetching": "Bilgiler getiriliyor…",
        "preview_error": "Önizleme alınamadı, bağlantıyı kontrol edin.",
        "unknown_title": "Bilinmeyen Video",
        "unknown_channel": "Bilinmeyen Kanal",
        "playlist_prefix": "Oynatma Listesi",
        "playlist_hint": "Tüm listeyi eklemek için “Kuyruğa Ekle”ye basın",
        "video_toggle": "Video",
        "audio_toggle": "Ses",
        "quality_best": "En Yüksek Kalite",
        "change_folder": "Değiştir",
        "open_folder": "Klasörü Aç",
        "tab_queue": "Kuyruk",
        "tab_history": "Geçmiş",
        "remove_selected": "Seçileni Sil",
        "clear_queue": "Kuyruğu Temizle",
        "status_ready": "Hazır",
        "status_waiting": "Bekliyor",
        "status_downloading": "İndiriliyor",
        "status_processing": "İşleniyor",
        "status_paused": "Duraklatıldı",
        "status_resumed": "Devam ediyor…",
        "status_completed": "Tamamlandı",
        "status_error": "Hata",
        "status_cancelled": "İptal edildi",
        "status_queue_done": "Kuyruk tamamlandı 🎉",
        "status_downloading_item": "{title} indiriliyor…",
        "progress_line": "İndiriliyor  ·  %{percent}  ·  {downloaded}/{total}  ·  {speed}  ·  Kalan {eta}",
        "processing_line": "İşleniyor (birleştirme / dönüştürme)…",
        "start_button": "İndirmeyi Başlat",
        "pause_button": "Duraklat",
        "resume_button": "Devam Et",
        "cancel_button": "İptal Et",
        "warning_title": "Uyarı",
        "warning_no_url": "Lütfen bir YouTube bağlantısı girin.",
        "warning_empty_queue": "Kuyruk boş. Önce bir video ekleyin.",
        "added_title": "Eklendi",
        "added_message": "{count} video kuyruğa eklendi.",
        "folder_error": "Klasör açılamadı:\n{error}",
        "select_folder_title": "Kayıt Klasörü Seç",
        "success_message": "İndirme başarıyla tamamlandı!",
        "cancelled_message": "İptal edildi.",
        "lang_switch_label": "EN",
    },
    "en": {
        "window_title": "Studio Downloader",
        "app_title": "Studio Downloader",
        "app_subtitle": "Download videos and music in seconds",
        "url_placeholder": "Paste a YouTube video or playlist link…",
        "paste": "Paste",
        "add_queue": "Add to Queue",
        "preview_title_empty": "No link yet",
        "preview_subtitle_empty": "Paste a video or playlist link above to get started",
        "preview_fetching": "Fetching details…",
        "preview_error": "Couldn't load preview, check the link.",
        "unknown_title": "Unknown Video",
        "unknown_channel": "Unknown Channel",
        "playlist_prefix": "Playlist",
        "playlist_hint": "Tap “Add to Queue” to queue the whole playlist",
        "video_toggle": "Video",
        "audio_toggle": "Audio",
        "quality_best": "Highest Quality",
        "change_folder": "Change",
        "open_folder": "Open Folder",
        "tab_queue": "Queue",
        "tab_history": "History",
        "remove_selected": "Remove Selected",
        "clear_queue": "Clear Queue",
        "status_ready": "Ready",
        "status_waiting": "Waiting",
        "status_downloading": "Downloading",
        "status_processing": "Processing",
        "status_paused": "Paused",
        "status_resumed": "Resuming…",
        "status_completed": "Completed",
        "status_error": "Error",
        "status_cancelled": "Cancelled",
        "status_queue_done": "Queue finished 🎉",
        "status_downloading_item": "Downloading {title}…",
        "progress_line": "Downloading  ·  {percent}%  ·  {downloaded}/{total}  ·  {speed}  ·  ETA {eta}",
        "processing_line": "Processing (merging / converting)…",
        "start_button": "Start Download",
        "pause_button": "Pause",
        "resume_button": "Resume",
        "cancel_button": "Cancel",
        "warning_title": "Heads up",
        "warning_no_url": "Please enter a YouTube link first.",
        "warning_empty_queue": "Your queue is empty. Add a video first.",
        "added_title": "Added",
        "added_message": "{count} videos added to the queue.",
        "folder_error": "Couldn't open the folder:\n{error}",
        "select_folder_title": "Choose Save Folder",
        "success_message": "Download completed successfully!",
        "cancelled_message": "Cancelled.",
        "lang_switch_label": "TR",
    },
}

STATUS_ICON = {
    "waiting": "⏳",
    "downloading": "⬇️",
    "completed": "✅",
    "error": "❌",
}


def human_size(num_bytes):
    if not num_bytes:
        return "?"
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def add_shadow(widget, blur=28, alpha=140, x=0, y=6):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setColor(QColor(0, 0, 0, alpha))
    effect.setOffset(x, y)
    widget.setGraphicsEffect(effect)


# ---------------------------------------------------------------------------
# Video / Playlist bilgilerini arka planda çeken thread
# ---------------------------------------------------------------------------
class InfoThread(QThread):
    info_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': 'in_playlist',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if not info:
                self.error_signal.emit("Bilgi alınamadı.")
                return

            if info.get('_type') == 'playlist' or info.get('entries') is not None:
                entries = [e for e in (info.get('entries') or []) if e]
                videos = []
                for e in entries:
                    vid_url = e.get('url')
                    if not vid_url and e.get('id'):
                        vid_url = f"https://www.youtube.com/watch?v={e.get('id')}"
                    if not vid_url:
                        continue
                    videos.append({
                        'url': vid_url,
                        'title': e.get('title') or None,
                        'duration': e.get('duration') or 0,
                    })
                data = {
                    'is_playlist': True,
                    'playlist_title': info.get('title') or None,
                    'videos': videos,
                }
                self.info_signal.emit(data)
                return

            thumb_url = info.get('thumbnail', '')
            thumb_data = None
            if thumb_url:
                try:
                    req = urllib.request.Request(
                        thumb_url, 
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        thumb_data = resp.read()
                except Exception:
                    thumb_data = None

            data = {
                'is_playlist': False,
                'title': info.get('title') or None,
                'uploader': info.get('uploader') or info.get('channel') or None,
                'duration': info.get('duration', 0),
                'thumbnail_data': thumb_data,
                'url': self.url,
            }
            self.info_signal.emit(data)
        except Exception as e:
            self.error_signal.emit(str(e))


# ---------------------------------------------------------------------------
# İndirme işlemini yürüten thread (duraklatma / iptal destekli)
# Not: dile bağlı metinler burada üretilmez; sadece ham veri/durum kodu
# gönderilir, arayüz bunu aktif dile göre biçimlendirir.
# ---------------------------------------------------------------------------
class DownloadThread(QThread):
    progress_signal = pyqtSignal(str, dict)      # kind: 'downloading' | 'processing', payload
    status_signal = pyqtSignal(str)              # 'paused' | 'resumed'
    finished_signal = pyqtSignal(str, str, str)  # 'success' | 'cancelled' | 'error', detail, title

    def __init__(self, url, title, download_type, quality, audio_quality, save_path):
        super().__init__()
        self.url = url
        self.title = title
        self.download_type = download_type
        self.quality = quality
        self.audio_quality = audio_quality
        self.save_path = save_path

        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancelled = False

    def request_pause(self):
        self.pause_event.clear()
        self.status_signal.emit("paused")

    def request_resume(self):
        self.pause_event.set()
        self.status_signal.emit("resumed")

    def request_cancel(self):
        self.cancelled = True
        self.pause_event.set()

    def run(self):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

            if self.download_type == "audio":
                bitrate = self.audio_quality.replace("kbps", "").strip()
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': bitrate,
                    }],
                })
            else:
                if self.quality == "1080p":
                    fmt = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best'
                elif self.quality == "720p":
                    fmt = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best'
                elif self.quality == "480p":
                    fmt = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best'
                elif self.quality == "360p":
                    fmt = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best'
                else:
                    fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
                ydl_opts.update({'format': fmt, 'merge_output_format': 'mp4'})

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if self.cancelled:
                self.finished_signal.emit("cancelled", "", self.title)
            else:
                self.finished_signal.emit("success", "", self.title)
        except Exception as e:
            if self.cancelled:
                self.finished_signal.emit("cancelled", "", self.title)
            else:
                self.finished_signal.emit("error", str(e), self.title)

    def progress_hook(self, d):
        if self.cancelled:
            raise yt_dlp.utils.DownloadError("cancelled by user")

        if not self.pause_event.is_set():
            self.pause_event.wait()
            if self.cancelled:
                raise yt_dlp.utils.DownloadError("cancelled by user")

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                payload = {
                    'percent': percent,
                    'downloaded': human_size(downloaded),
                    'total': human_size(total),
                    'speed': d.get('_speed_str', 'N/A').strip(),
                    'eta': d.get('_eta_str', 'N/A').strip(),
                }
                self.progress_signal.emit('downloading', payload)
        elif d['status'] == 'finished':
            self.progress_signal.emit('processing', {'percent': 100.0})


# ---------------------------------------------------------------------------
# Ana Pencere
# ---------------------------------------------------------------------------
class ModernDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.lang = "tr"

        self.queue = []      # [{'url','title','status_code'}]
        self.history = []    # [{'title','result','detail','time'}]

        self.current_thread = None
        self.processing_queue = False
        self._pending_playlist = None
        self._pending_single = None

        self.url_debounce = QTimer(self)
        self.url_debounce.setSingleShot(True)
        self.url_debounce.timeout.connect(self.fetch_info)

        self.init_ui()
        self.apply_theme()
        self.retranslate_ui()

    def t(self, key, **kwargs):
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    # ------------------------------------------------------------------
    # UI Kurulumu
    # ------------------------------------------------------------------
    def init_ui(self):
        self.setMinimumSize(820, 780)
        self.resize(860, 820)

        central_widget = QWidget(self)
        central_widget.setObjectName("rootBg")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # ---------- Header ----------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        logo = QLabel("▶")
        logo.setObjectName("logoBadge")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)
        header_row.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.app_title_label = QLabel()
        self.app_title_label.setObjectName("appTitle")
        self.app_subtitle_label = QLabel()
        self.app_subtitle_label.setObjectName("appSubtitle")
        title_col.addWidget(self.app_title_label)
        title_col.addWidget(self.app_subtitle_label)
        header_row.addLayout(title_col)

        header_row.addStretch()

        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("iconBtn")
        self.lang_btn.setFixedSize(44, 44)
        self.lang_btn.clicked.connect(self.toggle_language)
        header_row.addWidget(self.lang_btn)

        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("iconBtn")
        self.theme_btn.setFixedSize(44, 44)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_row.addWidget(self.theme_btn)

        main_layout.addLayout(header_row)

        # ---------- URL Card ----------
        url_card = QFrame()
        url_card.setObjectName("card")
        url_card_layout = QHBoxLayout(url_card)
        url_card_layout.setContentsMargins(16, 12, 12, 12)
        url_card_layout.setSpacing(10)

        link_icon = QLabel("🔗")
        link_icon.setObjectName("inlineIcon")
        url_card_layout.addWidget(link_icon)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.textChanged.connect(self.on_url_changed)
        url_card_layout.addWidget(self.url_input, 1)

        self.paste_btn = QPushButton()
        self.paste_btn.setObjectName("ghostBtn")
        self.paste_btn.clicked.connect(self.paste_clipboard)
        url_card_layout.addWidget(self.paste_btn)

        self.add_queue_btn = QPushButton()
        self.add_queue_btn.setObjectName("accentPillBtn")
        self.add_queue_btn.clicked.connect(self.add_to_queue)
        url_card_layout.addWidget(self.add_queue_btn)

        add_shadow(url_card)
        main_layout.addWidget(url_card)

        # ---------- Preview Card ----------
        self.preview_card = QFrame()
        self.preview_card.setObjectName("card")
        preview_layout = QHBoxLayout(self.preview_card)
        preview_layout.setContentsMargins(14, 14, 18, 14)
        preview_layout.setSpacing(16)

        self.thumb_label = QLabel("🎬")
        self.thumb_label.setFixedSize(150, 90)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setObjectName("thumb")
        preview_layout.addWidget(self.thumb_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("previewTitle")

        self.channel_label = QLabel()
        self.channel_label.setObjectName("subtleLabel")

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.channel_label)
        info_layout.addStretch()
        preview_layout.addLayout(info_layout, 1)

        add_shadow(self.preview_card)
        main_layout.addWidget(self.preview_card)

        # ---------- Options Card ----------
        options_card = QFrame()
        options_card.setObjectName("card")
        options_outer = QVBoxLayout(options_card)
        options_outer.setContentsMargins(16, 14, 16, 14)
        options_outer.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        segment = QFrame()
        segment.setObjectName("segment")
        segment_layout = QHBoxLayout(segment)
        segment_layout.setContentsMargins(4, 4, 4, 4)
        segment_layout.setSpacing(4)

        self.video_toggle = QPushButton()
        self.audio_toggle = QPushButton()
        for b in (self.video_toggle, self.audio_toggle):
            b.setCheckable(True)
            b.setObjectName("segmentBtn")
        self.video_toggle.setChecked(True)

        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        self.type_group.addButton(self.video_toggle, 0)
        self.type_group.addButton(self.audio_toggle, 1)
        self.type_group.idClicked.connect(self.on_type_changed)

        segment_layout.addWidget(self.video_toggle)
        segment_layout.addWidget(self.audio_toggle)
        row1.addWidget(segment)

        self.quality_combo = QComboBox()
        self.quality_combo.setObjectName("pillCombo")

        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.setObjectName("pillCombo")
        self.audio_quality_combo.addItems(["320 kbps", "192 kbps", "128 kbps"])

        self.option_stack = QStackedWidget()
        self.option_stack.addWidget(self.quality_combo)
        self.option_stack.addWidget(self.audio_quality_combo)
        row1.addWidget(self.option_stack, 1)

        options_outer.addLayout(row1)

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        options_outer.addWidget(divider)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.save_dir = os.path.expanduser("~/Downloads")
        folder_icon = QLabel("📁")
        folder_icon.setObjectName("inlineIcon")
        row2.addWidget(folder_icon)

        self.path_label = QLabel(self.save_dir)
        self.path_label.setObjectName("subtleLabel")
        row2.addWidget(self.path_label, 1)

        self.path_button = QPushButton()
        self.path_button.setObjectName("ghostBtn")
        self.path_button.clicked.connect(self.select_folder)
        row2.addWidget(self.path_button)

        self.open_folder_button = QPushButton()
        self.open_folder_button.setObjectName("ghostBtn")
        self.open_folder_button.clicked.connect(self.open_folder)
        row2.addWidget(self.open_folder_button)

        options_outer.addLayout(row2)

        add_shadow(options_card)
        main_layout.addWidget(options_card)

        # ---------- Queue / History Card ----------
        list_card = QFrame()
        list_card.setObjectName("card")
        list_card_layout = QVBoxLayout(list_card)
        list_card_layout.setContentsMargins(10, 10, 10, 12)
        list_card_layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("modernTabs")

        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        queue_layout.setContentsMargins(4, 8, 4, 4)
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("modernList")
        queue_layout.addWidget(self.queue_list)
        queue_btn_row = QHBoxLayout()
        self.remove_selected_btn = QPushButton()
        self.remove_selected_btn.setObjectName("ghostBtn")
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.clear_queue_btn = QPushButton()
        self.clear_queue_btn.setObjectName("ghostBtn")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_btn_row.addWidget(self.remove_selected_btn)
        queue_btn_row.addWidget(self.clear_queue_btn)
        queue_btn_row.addStretch()
        queue_layout.addLayout(queue_btn_row)
        self.tabs.addTab(queue_tab, "")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(4, 8, 4, 4)
        self.history_list = QListWidget()
        self.history_list.setObjectName("modernList")
        history_layout.addWidget(self.history_list)
        self.tabs.addTab(history_tab, "")

        list_card_layout.addWidget(self.tabs)
        add_shadow(list_card)
        main_layout.addWidget(list_card, 1)

        # ---------- Progress ----------
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgress")
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setObjectName("subtleLabel")
        main_layout.addWidget(self.status_label)

        # ---------- Controls ----------
        control_row = QHBoxLayout()
        control_row.setSpacing(10)

        self.download_button = QPushButton()
        self.download_button.setFixedHeight(48)
        self.download_button.setObjectName("primaryBtn")
        self.download_button.clicked.connect(self.start_queue_download)
        control_row.addWidget(self.download_button, 3)

        self.pause_button = QPushButton()
        self.pause_button.setFixedHeight(48)
        self.pause_button.setObjectName("secondaryBtn")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        control_row.addWidget(self.pause_button, 2)

        self.cancel_button = QPushButton()
        self.cancel_button.setFixedHeight(48)
        self.cancel_button.setObjectName("dangerBtn")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        control_row.addWidget(self.cancel_button, 2)

        main_layout.addLayout(control_row)

        self.on_type_changed(0)

    # ------------------------------------------------------------------
    # Dil
    # ------------------------------------------------------------------
    def toggle_language(self):
        self.lang = "en" if self.lang == "tr" else "tr"
        self.retranslate_ui()

    def retranslate_ui(self):
        lang = self.lang
        self.setWindowTitle(self.t("window_title"))
        self.lang_btn.setText(self.t("lang_switch_label"))

        self.app_title_label.setText(self.t("app_title"))
        self.app_subtitle_label.setText(self.t("app_subtitle"))

        self.url_input.setPlaceholderText(self.t("url_placeholder"))
        self.paste_btn.setText(self.t("paste"))
        self.add_queue_btn.setText("➕  " + self.t("add_queue"))

        # Önizleme: yalnızca hiçbir video yüklenmemişse varsayılan metni göster
        if not self._pending_single and not self._pending_playlist:
            self.title_label.setText(self.t("preview_title_empty"))
            self.channel_label.setText(self.t("preview_subtitle_empty"))
        elif self._pending_playlist:
            self._render_playlist_preview(self._pending_playlist)
        elif self._pending_single:
            self._render_single_preview(self._pending_single)

        self.video_toggle.setText("🎞️  " + self.t("video_toggle"))
        self.audio_toggle.setText("🎵  " + self.t("audio_toggle"))

        current_quality_idx = self.quality_combo.currentIndex()
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItems([self.t("quality_best"), "1080p", "720p", "480p", "360p"])
        self.quality_combo.setCurrentIndex(max(current_quality_idx, 0))
        self.quality_combo.blockSignals(False)

        self.path_button.setText(self.t("change_folder"))
        self.open_folder_button.setText(self.t("open_folder"))

        self.tabs.setTabText(0, self.t("tab_queue"))
        self.tabs.setTabText(1, self.t("tab_history"))
        self.remove_selected_btn.setText(self.t("remove_selected"))
        self.clear_queue_btn.setText(self.t("clear_queue"))

        if not self.processing_queue:
            self.status_label.setText(self.t("status_ready"))

        self.download_button.setText("▶  " + self.t("start_button"))
        is_paused = self.current_thread is not None and not self.current_thread.pause_event.is_set()
        self.pause_button.setText(("▶  " + self.t("resume_button")) if is_paused else ("⏸  " + self.t("pause_button")))
        self.cancel_button.setText("⏹  " + self.t("cancel_button"))

        self._rerender_queue()
        self._rerender_history()

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
        self.setStyleSheet(self._dark_qss() if self.dark_mode else self._light_qss())

    def _base_qss(self, root_bg, card, card_border, text, subtle, input_bg,
                   input_border, list_bg, list_hover, divider, segment_bg,
                   segment_btn_hover, thumb_bg, tab_bg):
        return f"""
            #rootBg {{ background-color: {root_bg}; }}
            QMainWindow {{ background-color: {root_bg}; }}
            QWidget {{ color: {text}; font-family: 'Segoe UI', 'Inter', Arial; font-size: 13px; }}

            #appTitle {{ font-size: 19px; font-weight: 800; color: {text}; }}
            #appSubtitle {{ font-size: 12px; color: {subtle}; }}
            #subtleLabel {{ color: {subtle}; font-size: 12px; }}
            #previewTitle {{ font-size: 14px; font-weight: 700; color: {text}; }}
            #inlineIcon {{ font-size: 15px; }}

            #logoBadge {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                border-radius: 14px; font-size: 18px; color: white;
            }}

            #card {{
                background-color: {card};
                border: 1px solid {card_border};
                border-radius: 16px;
            }}

            #thumb {{
                background-color: {thumb_bg};
                border-radius: 12px;
                font-size: 26px;
                color: {subtle};
            }}

            #divider {{ background-color: {divider}; border: none; }}

            QLineEdit#urlInput {{
                background: transparent;
                border: none;
                font-size: 13px;
                padding: 8px 4px;
                color: {text};
            }}

            QPushButton {{
                border: none;
                font-weight: 600;
            }}

            #iconBtn {{
                background-color: {card};
                border: 1px solid {card_border};
                border-radius: 22px;
                font-size: 14px;
            }}
            #iconBtn:hover {{ background-color: {segment_btn_hover}; }}

            #ghostBtn {{
                background-color: transparent;
                color: {subtle};
                border: 1px solid {card_border};
                border-radius: 10px;
                padding: 8px 14px;
            }}
            #ghostBtn:hover {{ background-color: {segment_btn_hover}; color: {text}; }}

            #accentPillBtn {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                color: white;
                border-radius: 10px;
                padding: 9px 18px;
            }}
            #accentPillBtn:hover {{ background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed); }}

            #segment {{
                background-color: {segment_bg};
                border-radius: 12px;
            }}
            #segmentBtn {{
                background-color: transparent;
                color: {subtle};
                border-radius: 9px;
                padding: 9px 16px;
            }}
            #segmentBtn:checked {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                color: white;
            }}
            #segmentBtn:hover:!checked {{ background-color: {segment_btn_hover}; }}

            QComboBox#pillCombo {{
                background-color: {input_bg};
                border: 1px solid {input_border};
                border-radius: 10px;
                padding: 9px 14px;
                min-width: 140px;
                color: {text};
            }}
            QComboBox#pillCombo::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {text};
                border: 1px solid {input_border};
                selection-background-color: {ACCENT_A};
                selection-color: white;
                outline: none;
            }}

            QListWidget#modernList {{
                background-color: {list_bg};
                border: none;
                border-radius: 10px;
                padding: 4px;
            }}
            QListWidget#modernList::item {{
                padding: 9px 10px;
                border-radius: 8px;
                margin: 2px 0px;
            }}
            QListWidget#modernList::item:selected {{
                background-color: {list_hover};
                color: {text};
            }}
            QListWidget#modernList::item:hover {{
                background-color: {list_hover};
            }}

            QTabWidget#modernTabs::pane {{
                border: none;
                background: transparent;
                top: 4px;
            }}
            QTabBar::tab {{
                background: {tab_bg};
                color: {subtle};
                padding: 8px 18px;
                border-radius: 9px;
                margin-right: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                color: white;
            }}

            QProgressBar#modernProgress {{
                background-color: {segment_bg};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar#modernProgress::chunk {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                border-radius: 5px;
            }}

            #primaryBtn {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_A}, stop:1 {ACCENT_B});
                color: white;
                border-radius: 14px;
                font-size: 14px;
            }}
            #primaryBtn:hover {{ background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed); }}
            #primaryBtn:disabled {{ background-color: {card_border}; color: {subtle}; }}

            #secondaryBtn {{
                background-color: {card};
                border: 1px solid {card_border};
                color: {text};
                border-radius: 14px;
                font-size: 14px;
            }}
            #secondaryBtn:hover {{ background-color: {segment_btn_hover}; }}
            #secondaryBtn:disabled {{ color: {subtle}; }}

            #dangerBtn {{
                background-color: transparent;
                border: 1px solid #ef4444;
                color: #ef4444;
                border-radius: 14px;
                font-size: 14px;
            }}
            #dangerBtn:hover {{ background-color: rgba(239,68,68,0.12); }}
            #dangerBtn:disabled {{ border-color: {card_border}; color: {subtle}; }}

            QScrollBar:vertical {{ background: transparent; width: 8px; }}
            QScrollBar::handle:vertical {{ background: {card_border}; border-radius: 4px; }}
        """

    def _dark_qss(self):
        return self._base_qss(
            root_bg="#0b0b0f", card="#16161c", card_border="#26262f",
            text="#f4f4f6", subtle="#9a9aa5", input_bg="#1e1e26", input_border="#2c2c36",
            list_bg="#101014", list_hover="#24242e", divider="#232330",
            segment_bg="#1e1e26", segment_btn_hover="#26262f", thumb_bg="#0b0b0f",
            tab_bg="#1e1e26",
        )

    def _light_qss(self):
        return self._base_qss(
            root_bg="#f6f6f9", card="#ffffff", card_border="#e6e6ec",
            text="#17171c", subtle="#75758a", input_bg="#f2f2f7", input_border="#e6e6ec",
            list_bg="#fafafc", list_hover="#eeeef7", divider="#eeeef2",
            segment_bg="#f0f0f6", segment_btn_hover="#e6e6f2", thumb_bg="#f0f0f6",
            tab_bg="#f0f0f6",
        )

    # ------------------------------------------------------------------
    # URL / Bilgi çekme
    # ------------------------------------------------------------------
    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)

    def on_url_changed(self, text):
        self.url_debounce.stop()
        if not text.strip():
            return
        self.title_label.setText(self.t("preview_fetching"))
        self.url_debounce.start(600)

    def fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return
        
        valid_domains = ["youtube.com", "youtu.be", "tiktok.com"]
        if not any(domain in url for domain in valid_domains):
            self.title_label.setText("Desteklenmeyen bağlantı!")
            return

        # Eski veriyi temizle
        self._pending_single = None
        self._pending_playlist = None

        self.info_thread = InfoThread(url)
        self.info_thread.info_signal.connect(self.display_info)
        self.info_thread.error_signal.connect(lambda msg: (self.title_label.setText(self.t("preview_error")), print(f"[Önizleme Hatası]: {msg}")))
        self.info_thread.start()

    def _render_playlist_preview(self, data):
        title = data.get('playlist_title') or self.t("playlist_prefix")
        count = len(data['videos'])
        self.title_label.setText(f"📃 {self.t('playlist_prefix')}: {title}  ·  {count}")
        self.channel_label.setText(self.t("playlist_hint"))
        self.thumb_label.setText("📃")
        self.thumb_label.setPixmap(QPixmap())

    def _render_single_preview(self, data):
        title = data.get('title') or self.t("unknown_title")
        uploader = data.get('uploader') or self.t("unknown_channel")
        self.title_label.setText(title)
        mins, secs = divmod(int(data.get('duration', 0) or 0), 60)
        self.channel_label.setText(f"{uploader}  ·  {mins:02d}:{secs:02d}")
        thumb_data = data.get('thumbnail_data')
        if thumb_data:
            image = QImage()
            image.loadFromData(thumb_data)
            pixmap = QPixmap.fromImage(image).scaled(
                150, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.thumb_label.setPixmap(pixmap)
        else:
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("🎬")

    def display_info(self, data):
        if data.get('is_playlist'):
            self._pending_playlist = data
            self._pending_single = None
            self._render_playlist_preview(data)
        else:
            self._pending_single = data
            self._pending_playlist = None
            self._render_single_preview(data)

    def add_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, self.t("warning_title"), self.t("warning_no_url"))
            return

        valid_domains = ["youtube.com", "youtu.be", "tiktok.com"]
        if not any(domain in url for domain in valid_domains):
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir YouTube veya TikTok linki girin!")
            return

        playlist = self._pending_playlist
        single = self._pending_single

        # Playlist ise tüm videoları ekle
        if playlist and playlist.get('videos'):
            for v in playlist['videos']:
                self._append_queue_item(v['url'], v['title'] or self.t("unknown_title"))
            QMessageBox.information(
                self, self.t("added_title"), self.t("added_message", count=len(playlist['videos']))
            )
        # Tek video bilgisi geldiyse
        elif single and single.get('url') == url:
            self._append_queue_item(single['url'], single.get('title') or self.t("unknown_title"))
        # Önizleme patlamış olsa bile linki doğrudan kuyruğa ekle!
        else:
            fallback_title = "Video (" + url.split("?")[0].rstrip("/").split("/")[-1] + ")"
            self._append_queue_item(url, fallback_title)

        # Yeni link eklenebilsin diye temizlik
        self._pending_single = None
        self._pending_playlist = None
        self.url_input.clear()

    def _append_queue_item(self, url, title):
        item = {'url': url, 'title': title, 'status_code': 'waiting'}
        self.queue.append(item)
        self.queue_list.addItem(QListWidgetItem(self._queue_item_text(item)))

    def _queue_item_text(self, item):
        icon = STATUS_ICON.get(item['status_code'], "⏳")
        status_word = self.t(f"status_{item['status_code']}")
        return f"{icon}  {item['title']}  —  {status_word}"

    def _rerender_queue(self):
        for row, item in enumerate(self.queue):
            list_item = self.queue_list.item(row)
            if list_item:
                list_item.setText(self._queue_item_text(item))

    def _history_item_text(self, entry):
        icon = "✅" if entry['result'] == 'success' else "❌"
        status_word = self.t("status_completed") if entry['result'] == 'success' else self.t("status_error")
        detail = entry['detail'] if entry['detail'] else status_word
        return f"{icon}  {entry['title']}   ·   {entry['time']}   ·   {detail}"

    def _rerender_history(self):
        self.history_list.clear()
        for entry in self.history:
            self.history_list.addItem(QListWidgetItem(self._history_item_text(entry)))

    def remove_selected(self):
        row = self.queue_list.currentRow()
        if row >= 0:
            self.queue_list.takeItem(row)
            del self.queue[row]

    def clear_queue(self):
        self.queue_list.clear()
        self.queue.clear()

    def on_type_changed(self, button_id):
        is_audio = (button_id == 1)
        self.option_stack.setCurrentIndex(1 if is_audio else 0)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.t("select_folder_title"), self.save_dir)
        if folder:
            self.save_dir = folder
            self.path_label.setText(self.save_dir)

    def open_folder(self):
        path = self.save_dir
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, self.t("warning_title"), self.t("folder_error", error=e))

    # ------------------------------------------------------------------
    # İndirme kuyruğu yönetimi
    # ------------------------------------------------------------------
    def start_queue_download(self):
        if not self.queue:
            QMessageBox.warning(self, self.t("warning_title"), self.t("warning_empty_queue"))
            return
        if self.processing_queue:
            return

        self.processing_queue = True
        self.download_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("⏸  " + self.t("pause_button"))
        self.cancel_button.setEnabled(True)
        self._queue_index = 0
        self._download_next()

    def _download_next(self):
        # Kuyrukta eleman kalmadıysa bitir
        if not self.queue:
            self.processing_queue = False
            self.download_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.status_label.setText(self.t("status_queue_done"))
            return

        # Listenin her zaman ilk elemanını (en baştakini) indir
        item = self.queue[0]
        item['status_code'] = 'downloading'
        self._rerender_queue()
        self.progress_bar.setValue(0)
        self.status_label.setText(self.t("status_downloading_item", title=item['title']))

        download_type = "audio" if self.audio_toggle.isChecked() else "video"
        quality = self.quality_combo.currentText()
        audio_quality = self.audio_quality_combo.currentText().replace(" ", "")

        self.current_thread = DownloadThread(
            item['url'], item['title'], download_type, quality, audio_quality, self.save_dir
        )
        self.current_thread.progress_signal.connect(self.update_progress)
        self.current_thread.status_signal.connect(self.update_status_only)
        self.current_thread.finished_signal.connect(self._on_item_finished)
        self.current_thread.start()

    def _on_item_finished(self, result, detail, title):
        # Geçmişe (History) ekle
        self.history.append({
            'title': title,
            'result': result if result != 'cancelled' else 'error',
            'detail': self.t("cancelled_message") if result == 'cancelled'
                      else (self.t("success_message") if result == 'success' else detail),
            'time': datetime.now().strftime('%H:%M:%S'),
        })
        self._rerender_history()

        # İster başarılı olsun ister hatalı, indirilen ilk elemanı kuyruktan ve ekrandan SİL
        if self.queue:
            del self.queue[0]
            self.queue_list.takeItem(0)

        # İptal edildiyse kuyruk işlemeyi durdur
        if result == 'cancelled':
            self.processing_queue = False
            self.download_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.status_label.setText(self.t("status_cancelled"))
            return

        # Bir sonraki videoya geç (artık o en başa kaymış oldu)
        self._download_next()

    def _on_item_finished(self, result, detail, title):
        # Geçmişe kaydet
        self.history.append({
            'title': title,
            'result': result if result != 'cancelled' else 'error',
            'detail': self.t("cancelled_message") if result == 'cancelled'
                      else (self.t("success_message") if result == 'success' else detail),
            'time': datetime.now().strftime('%H:%M:%S'),
        })
        self._rerender_history()

        # SADECE BAŞARILIYSA KUYRUKTAN SİL
        if result == 'success':
            if self.queue:
                del self.queue[0]
                self.queue_list.takeItem(0)
        else:
            # Hata aldıysa durumunu 'error' yap ve yerinde kalsın
            if self.queue:
                self.queue[0]['status_code'] = 'error'
                self._rerender_queue()

        # İptal veya hata durumunda süreci durdur (arka arkaya patlamasın)
        if result in ('cancelled', 'error'):
            self.processing_queue = False
            self.download_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            if result == 'error':
                self.status_label.setText(f"Hata: {detail[:45]}..." if detail else self.t("status_error"))
            else:
                self.status_label.setText(self.t("status_cancelled"))
            return

        # Başarılı olduysa sıradakine geç
        self._download_next()

    def update_progress(self, kind, payload):
        percent = payload.get('percent', 0)
        self.progress_bar.setValue(int(percent))
        if kind == 'downloading':
            self.status_label.setText(self.t(
                "progress_line",
                percent=f"{percent:.1f}",
                downloaded=payload.get('downloaded', '?'),
                total=payload.get('total', '?'),
                speed=payload.get('speed', 'N/A'),
                eta=payload.get('eta', 'N/A'),
            ))
        else:
            self.status_label.setText(self.t("processing_line"))

    def update_status_only(self, code):
        self.status_label.setText(self.t(f"status_{code}"))

    def toggle_pause(self):
        if not self.current_thread:
            return
        if self.current_thread.pause_event.is_set():
            self.current_thread.request_pause()
            self.pause_button.setText("▶  " + self.t("resume_button"))
        else:
            self.current_thread.request_resume()
            self.pause_button.setText("⏸  " + self.t("pause_button"))

    def cancel_download(self):
        if self.current_thread:
            self.current_thread.request_cancel()
        self.cancel_button.setEnabled(False)

    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.request_cancel()
            self.current_thread.wait(2000)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernDownloader()
    window.show()
    sys.exit(app.exec_())
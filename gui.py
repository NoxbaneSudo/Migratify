"""
Migratify GUI — Modern Desktop Interface
Built with CustomTkinter for a premium dark-theme experience.
All migration logic reused from migrate.py core functions.
"""

# === Auto-install GUI dependencies ===
import sys
import subprocess

GUI_DEPS = ["customtkinter", "ytmusicapi", "colorama", "tqdm"]

def _ensure_gui_deps():
    import importlib
    missing = []
    for pkg in GUI_DEPS:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[Migratify GUI] Installing: {', '.join(missing)}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

_ensure_gui_deps()
# === End auto-install ===

import os
import re
import csv
import json
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup_browser

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "library.csv")
HEADERS_PATH = os.path.join(BASE_DIR, "headers.txt")
AUTH_JSON_PATH = os.path.join(BASE_DIR, "oauth.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "progress.json")
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
FAILED_CSV_PATH = os.path.join(BASE_DIR, "failed_songs.csv")
BATCH_DIR = os.path.join(BASE_DIR, "csv_batch")

# ─── Theme ────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Migratify brand palette
BRAND_GREEN = "#00E676"
BRAND_DARK = "#0D1117"
BRAND_SURFACE = "#161B22"
BRAND_CARD = "#1C2333"
BRAND_BORDER = "#30363D"
BRAND_TEXT = "#E6EDF3"
BRAND_DIM = "#8B949E"
BRAND_RED = "#F85149"
BRAND_YELLOW = "#D29922"
BRAND_CYAN = "#58A6FF"

FONT_FAMILY = "Segoe UI"


# ═══════════════════════════════════════════════════════════════════
#  CORE LOGIC (shared with migrate.py)
# ═══════════════════════════════════════════════════════════════════

def load_headers(filepath):
    for enc in ['utf-8', 'utf-16', 'utf-8-sig', 'cp1251']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    try:
        with open(filepath, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore').strip()
    except Exception:
        return ""


def get_duration_sec(duration_str):
    if not duration_str:
        return None
    try:
        parts = str(duration_str).split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return None


def universal_csv_parser(filepath):
    songs = []
    try:
        with open(filepath, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return songs
            track_col = next(
                (k for k in reader.fieldnames
                 if k.lower() in ['track name', 'title', 'song', 'name', 'track']),
                None
            )
            artist_col = next(
                (k for k in reader.fieldnames
                 if k.lower() in [
                     'artist name(s)', 'artist', 'creator',
                     'artist name', 'artists'
                 ]),
                None
            )
            dur_col = next(
                (k for k in reader.fieldnames
                 if k.lower() in [
                     'track duration (ms)', 'duration',
                     'length', 'time (ms)', 'time'
                 ]),
                None
            )
            if not track_col and not artist_col:
                track_col = (reader.fieldnames[0]
                             if len(reader.fieldnames) > 0 else None)
                artist_col = (reader.fieldnames[1]
                              if len(reader.fieldnames) > 1 else None)
            for row in reader:
                track = row.get(track_col, "").strip() if track_col else ""
                artist = row.get(artist_col, "").strip() if artist_col else ""
                duration = row.get(dur_col, "") if dur_col else ""
                if track or artist:
                    target_sec = None
                    if str(duration).isdigit():
                        target_sec = int(duration) // 1000
                    elif ":" in str(duration):
                        target_sec = get_duration_sec(duration)
                    songs.append({
                        "track": track,
                        "artist": artist,
                        "target_sec": target_sec
                    })
    except Exception:
        pass
    return songs


def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_history(history_set):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(list(history_set), f)


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"migrated_count": 0, "processed_rows": 0, "failed_rows": 0}


def save_progress(progress):
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=4)


def log_failed_song(idx, query, reason):
    file_exists = os.path.isfile(FAILED_CSV_PATH)
    with open(FAILED_CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Track Index', 'Query', 'Reason'])
        writer.writerow([idx, query, reason])


def parse_curl(raw_content):
    """Parse cURL command into raw header lines for ytmusicapi."""
    low = raw_content.lower()
    if low.startswith("http"):
        return None, "You pasted a URL, not a cURL command."

    if low.startswith("curl"):
        lines = []
        header_matches = re.findall(r"-H '([^']+)'", raw_content)
        header_matches += re.findall(r'-H "([^"]+)"', raw_content)
        for h in header_matches:
            lines.append(h)
        cookie_matches = re.findall(r"-b '([^']+)'", raw_content)
        cookie_matches += re.findall(r'-b "([^"]+)"', raw_content)
        for c in cookie_matches:
            lines.append(f"cookie: {c}")
        if not lines:
            return None, "No headers found in cURL."
        raw_content = "\n".join(lines)

    low = raw_content.lower()
    if "cookie" not in low:
        return None, "Cookie header is missing."

    if "x-goog-authuser" not in low:
        raw_content += "\nx-goog-authuser: 0"

    return raw_content, None


# ═══════════════════════════════════════════════════════════════════
#  WIDGETS
# ═══════════════════════════════════════════════════════════════════

class GlowButton(ctk.CTkButton):
    """A button with a subtle glow-on-hover effect."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("height", 44)
        kwargs.setdefault("font", ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"))
        kwargs.setdefault("fg_color", BRAND_GREEN)
        kwargs.setdefault("text_color", BRAND_DARK)
        kwargs.setdefault("hover_color", "#33EB91")
        super().__init__(master, **kwargs)


class StatusCard(ctk.CTkFrame):
    """Stat card showing a label + value."""

    def __init__(self, master, label, value="0", color=BRAND_GREEN, **kwargs):
        super().__init__(master, fg_color=BRAND_CARD, corner_radius=12, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=BRAND_DIM
        )
        self.label.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")

        self.value_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=color
        )
        self.value_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

    def set_value(self, val):
        self.value_label.configure(text=str(val))


# ═══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════

class MigratifyApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Migratify — Music Migration Tool")
        self.geometry("960x680")
        self.minsize(800, 600)
        self.configure(fg_color=BRAND_DARK)

        # State
        self.ytm = None
        self.csv_path = None
        self.songs = []
        self.is_migrating = False
        self.stop_flag = False

        self._build_ui()
        self._check_auth_status()

    # ── Layout ────────────────────────────────────────────────────

    def _build_ui(self):
        # Grid layout: sidebar + main area
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=220, fg_color=BRAND_SURFACE,
                               corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_rowconfigure(8, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(20, 8), sticky="we")

        ctk.CTkLabel(
            logo_frame, text="⚡ Migratify",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=BRAND_GREEN
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="by NoxbaneSudo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=BRAND_DIM
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(sidebar, height=1, fg_color=BRAND_BORDER).grid(
            row=1, column=0, sticky="we", padx=16, pady=8)

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("🏠  Dashboard", "dashboard"),
            ("🚀  Migrate", "migrate"),
            ("📂  Batch Mode", "batch"),
            ("🛠  Fix Errors", "fix"),
            ("⚙️  Settings", "settings"),
        ]
        for i, (label, key) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color="transparent", text_color=BRAND_TEXT,
                hover_color=BRAND_CARD, height=38, corner_radius=8,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.grid(row=2 + i, column=0, padx=10, pady=2, sticky="we")
            self.nav_buttons[key] = btn

        # Auth indicator at bottom
        self.auth_indicator = ctk.CTkLabel(
            sidebar, text="● Disconnected",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=BRAND_RED
        )
        self.auth_indicator.grid(row=9, column=0, padx=16, pady=(0, 16),
                                 sticky="sw")

        # ── Main content ──────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self, fg_color=BRAND_DARK,
                                       corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Pages
        self.pages = {}
        self._build_dashboard_page()
        self._build_migrate_page()
        self._build_batch_page()
        self._build_fix_page()
        self._build_settings_page()

        self._switch_tab("dashboard")

    # ── Pages ─────────────────────────────────────────────────────

    def _build_dashboard_page(self):
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        page.grid_columnconfigure((0, 1, 2), weight=1)
        self.pages["dashboard"] = page

        # Header
        ctk.CTkLabel(
            page, text="Dashboard",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=BRAND_TEXT
        ).grid(row=0, column=0, columnspan=3, padx=24, pady=(24, 4),
               sticky="w")

        ctk.CTkLabel(
            page, text="Overview of your migration progress",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        ).grid(row=1, column=0, columnspan=3, padx=24, pady=(0, 16),
               sticky="w")

        # Stat cards
        self.card_migrated = StatusCard(page, "Migrated", "0", BRAND_GREEN)
        self.card_migrated.grid(row=2, column=0, padx=(24, 8), pady=8,
                                sticky="nswe")

        self.card_failed = StatusCard(page, "Failed", "0", BRAND_RED)
        self.card_failed.grid(row=2, column=1, padx=8, pady=8, sticky="nswe")

        self.card_total = StatusCard(page, "Total in CSV", "—", BRAND_CYAN)
        self.card_total.grid(row=2, column=2, padx=(8, 24), pady=8,
                             sticky="nswe")

        # Log area
        ctk.CTkLabel(
            page, text="Activity Log",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=BRAND_TEXT
        ).grid(row=3, column=0, columnspan=3, padx=24, pady=(20, 4),
               sticky="w")

        self.log_box = ctk.CTkTextbox(
            page, fg_color=BRAND_CARD, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=12, border_width=1, border_color=BRAND_BORDER,
            state="disabled"
        )
        self.log_box.grid(row=4, column=0, columnspan=3, padx=24,
                          pady=(0, 24), sticky="nswe")
        page.grid_rowconfigure(4, weight=1)

    def _build_migrate_page(self):
        page = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.pages["migrate"] = page

        ctk.CTkLabel(
            page, text="Single CSV Migration",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=24, pady=(24, 4), anchor="w")

        ctk.CTkLabel(
            page, text="Migrate tracks from a single CSV file to YouTube Music",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        ).pack(padx=24, pady=(0, 16), anchor="w")

        # CSV Selection
        csv_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        csv_card.pack(padx=24, pady=8, fill="x")

        ctk.CTkLabel(
            csv_card, text="📄 CSV File",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=16, pady=(12, 4), anchor="w")

        file_row = ctk.CTkFrame(csv_card, fg_color="transparent")
        file_row.pack(padx=16, pady=(0, 12), fill="x")

        self.csv_label = ctk.CTkLabel(
            file_row, text="No file selected",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_DIM
        )
        self.csv_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            file_row, text="Browse...", width=100, height=32,
            corner_radius=8, fg_color=BRAND_BORDER,
            hover_color=BRAND_CARD, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._browse_csv
        ).pack(side="right")

        # Options card
        opts_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        opts_card.pack(padx=24, pady=8, fill="x")

        ctk.CTkLabel(
            opts_card, text="⚙️ Options",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=16, pady=(12, 8), anchor="w")

        # Smart Search
        self.smart_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            opts_card, text="Smart Search (compare durations, ±90s tolerance)",
            variable=self.smart_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, progress_color=BRAND_GREEN
        ).pack(padx=16, pady=4, anchor="w")

        # Reverse order
        self.reverse_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            opts_card, text="Reverse Order (oldest tracks at top)",
            variable=self.reverse_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, progress_color=BRAND_GREEN
        ).pack(padx=16, pady=4, anchor="w")

        # Dry Run
        self.dryrun_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            opts_card, text="Dry Run (search only, no likes)",
            variable=self.dryrun_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, progress_color=BRAND_YELLOW
        ).pack(padx=16, pady=(4, 12), anchor="w")

        # Destination
        dest_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        dest_card.pack(padx=24, pady=8, fill="x")

        ctk.CTkLabel(
            dest_card, text="🎯 Destination",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=16, pady=(12, 8), anchor="w")

        self.dest_var = ctk.StringVar(value="liked")
        ctk.CTkRadioButton(
            dest_card, text="Liked Songs",
            variable=self.dest_var, value="liked",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN
        ).pack(padx=16, pady=4, anchor="w")

        ctk.CTkRadioButton(
            dest_card, text="Create New Playlist",
            variable=self.dest_var, value="new_playlist",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN
        ).pack(padx=16, pady=4, anchor="w")

        ctk.CTkRadioButton(
            dest_card, text="Existing Playlist",
            variable=self.dest_var, value="existing",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN
        ).pack(padx=16, pady=(4, 4), anchor="w")

        self.playlist_name_entry = ctk.CTkEntry(
            dest_card, placeholder_text="Playlist name...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=BRAND_SURFACE, border_color=BRAND_BORDER,
            corner_radius=8, height=36
        )
        self.playlist_name_entry.pack(padx=16, pady=(4, 12), fill="x")

        # Progress
        progress_card = ctk.CTkFrame(page, fg_color=BRAND_CARD,
                                     corner_radius=12)
        progress_card.pack(padx=24, pady=8, fill="x")

        self.progress_label = ctk.CTkLabel(
            progress_card, text="Ready to migrate",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        )
        self.progress_label.pack(padx=16, pady=(12, 4), anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_card, progress_color=BRAND_GREEN,
            fg_color=BRAND_SURFACE, corner_radius=6, height=10
        )
        self.progress_bar.pack(padx=16, pady=(0, 4), fill="x")
        self.progress_bar.set(0)

        self.current_track_label = ctk.CTkLabel(
            progress_card, text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=BRAND_DIM
        )
        self.current_track_label.pack(padx=16, pady=(0, 12), anchor="w")

        # Buttons
        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(padx=24, pady=16, fill="x")

        self.start_btn = GlowButton(
            btn_row, text="▶  START MIGRATION", width=200,
            command=self._start_migration
        )
        self.start_btn.pack(side="left")

        self.stop_btn = ctk.CTkButton(
            btn_row, text="⏹  STOP", width=100, height=44,
            corner_radius=12, fg_color=BRAND_RED, hover_color="#FF6B6B",
            text_color="white",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            command=self._stop_migration, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=8)

    def _build_batch_page(self):
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages["batch"] = page

        ctk.CTkLabel(
            page, text="Batch Migration",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=BRAND_TEXT
        ).grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")

        ctk.CTkLabel(
            page, text="Drop multiple CSVs into the csv_batch folder — "
                       "each file becomes a playlist",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        ).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        info_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        info_card.grid(row=2, column=0, padx=24, pady=8, sticky="we")

        ctk.CTkLabel(
            info_card,
            text="📂 How it works:\n\n"
                 "1. Click 'Open Folder' to create & open the csv_batch folder\n"
                 "2. Drag your CSV files into it (e.g. Rock.csv, Indie.csv)\n"
                 "3. Come back here and click 'Start Batch'\n"
                 "4. Each CSV will become a separate playlist named after the file",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_TEXT, justify="left"
        ).pack(padx=16, pady=16, anchor="w")

        self.batch_smart_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            info_card, text="Smart Search",
            variable=self.batch_smart_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_TEXT, progress_color=BRAND_GREEN
        ).pack(padx=16, pady=(0, 16), anchor="w")

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=24, pady=8, sticky="we")

        ctk.CTkButton(
            btn_row, text="📁  Open Folder", width=160, height=40,
            corner_radius=10, fg_color=BRAND_BORDER,
            hover_color=BRAND_CARD, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._open_batch_folder
        ).pack(side="left")

        self.batch_start_btn = GlowButton(
            btn_row, text="▶  Start Batch", width=160,
            command=self._start_batch
        )
        self.batch_start_btn.pack(side="left", padx=8)

        # Batch progress
        self.batch_progress_label = ctk.CTkLabel(
            page, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        )
        self.batch_progress_label.grid(row=4, column=0, padx=24, pady=(16, 4),
                                       sticky="w")

        self.batch_progress_bar = ctk.CTkProgressBar(
            page, progress_color=BRAND_GREEN,
            fg_color=BRAND_SURFACE, corner_radius=6, height=10
        )
        self.batch_progress_bar.grid(row=5, column=0, padx=24, pady=(0, 8),
                                     sticky="we")
        self.batch_progress_bar.set(0)

        # Log
        self.batch_log = ctk.CTkTextbox(
            page, fg_color=BRAND_CARD, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=12, border_width=1, border_color=BRAND_BORDER,
            state="disabled"
        )
        self.batch_log.grid(row=6, column=0, padx=24, pady=(0, 24),
                            sticky="nswe")
        page.grid_rowconfigure(6, weight=1)

    def _build_fix_page(self):
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages["fix"] = page

        ctk.CTkLabel(
            page, text="Fix Failed Songs",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=BRAND_TEXT
        ).grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")

        ctk.CTkLabel(
            page, text="Manually pick the correct track for songs that "
                       "weren't found automatically",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        ).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        GlowButton(
            page, text="🔄  Load Failed Songs", width=220,
            command=self._load_failed_songs
        ).grid(row=2, column=0, padx=24, pady=8, sticky="w")

        # Scrollable list of failed songs + search results
        self.fix_scroll = ctk.CTkScrollableFrame(
            page, fg_color="transparent"
        )
        self.fix_scroll.grid(row=3, column=0, padx=24, pady=8,
                             sticky="nswe")
        page.grid_rowconfigure(3, weight=1)

    def _build_settings_page(self):
        page = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.pages["settings"] = page

        ctk.CTkLabel(
            page, text="Settings",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=24, pady=(24, 4), anchor="w")

        ctk.CTkLabel(
            page, text="Configure YouTube Music authentication",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=BRAND_DIM
        ).pack(padx=24, pady=(0, 16), anchor="w")

        # Auth card
        auth_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        auth_card.pack(padx=24, pady=8, fill="x")

        ctk.CTkLabel(
            auth_card, text="🔑 YouTube Music Auth (cURL)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=16, pady=(12, 4), anchor="w")

        ctk.CTkLabel(
            auth_card,
            text="Paste your cURL (bash) from YouTube Music DevTools below.\n"
                 "F12 → Network → search 'browse' → "
                 "Right-click → Copy as cURL (bash)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=BRAND_DIM, justify="left"
        ).pack(padx=16, pady=(0, 8), anchor="w")

        self.curl_textbox = ctk.CTkTextbox(
            auth_card, height=160, fg_color=BRAND_SURFACE,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8, border_width=1, border_color=BRAND_BORDER
        )
        self.curl_textbox.pack(padx=16, pady=(0, 8), fill="x")

        btn_row = ctk.CTkFrame(auth_card, fg_color="transparent")
        btn_row.pack(padx=16, pady=(0, 12), fill="x")

        GlowButton(
            btn_row, text="🔗  Authenticate", width=180,
            command=self._authenticate
        ).pack(side="left")

        self.auth_status_label = ctk.CTkLabel(
            btn_row, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=BRAND_DIM
        )
        self.auth_status_label.pack(side="left", padx=12)

        # Reset card
        reset_card = ctk.CTkFrame(page, fg_color=BRAND_CARD, corner_radius=12)
        reset_card.pack(padx=24, pady=8, fill="x")

        ctk.CTkLabel(
            reset_card, text="🗑️ Reset",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(padx=16, pady=(12, 8), anchor="w")

        btns = ctk.CTkFrame(reset_card, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 12), fill="x")

        ctk.CTkButton(
            btns, text="Reset Progress", width=140, height=36,
            corner_radius=8, fg_color=BRAND_BORDER,
            hover_color=BRAND_RED, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._reset_progress
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="Reset Auth", width=140, height=36,
            corner_radius=8, fg_color=BRAND_BORDER,
            hover_color=BRAND_RED, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._reset_auth
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="Reset History", width=140, height=36,
            corner_radius=8, fg_color=BRAND_BORDER,
            hover_color=BRAND_RED, text_color=BRAND_TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._reset_history
        ).pack(side="left")

    # ── Navigation ────────────────────────────────────────────────

    def _switch_tab(self, tab_name):
        for key, page in self.pages.items():
            page.grid_forget()

        self.pages[tab_name].grid(row=0, column=0, sticky="nswe")

        for key, btn in self.nav_buttons.items():
            if key == tab_name:
                btn.configure(fg_color=BRAND_CARD, text_color=BRAND_GREEN)
            else:
                btn.configure(fg_color="transparent", text_color=BRAND_TEXT)

    # ── Logging ───────────────────────────────────────────────────

    def _log(self, msg, color=None):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _batch_log_msg(self, msg):
        self.batch_log.configure(state="normal")
        self.batch_log.insert("end", f"{msg}\n")
        self.batch_log.see("end")
        self.batch_log.configure(state="disabled")

    # ── Auth ──────────────────────────────────────────────────────

    def _check_auth_status(self):
        if os.path.exists(AUTH_JSON_PATH):
            try:
                self.ytm = YTMusic(AUTH_JSON_PATH)
                self.auth_indicator.configure(
                    text="● Connected", text_color=BRAND_GREEN)
                self._log("✅ YouTube Music authenticated.")

                # Auto-load default CSV if exists
                for p in [CSV_PATH, os.path.join(BASE_DIR, "liked.csv")]:
                    if os.path.exists(p):
                        self.csv_path = p
                        songs = universal_csv_parser(p)
                        self.songs = songs
                        self.csv_label.configure(
                            text=os.path.basename(p),
                            text_color=BRAND_GREEN
                        )
                        self.card_total.set_value(str(len(songs)))
                        self._log(f"📄 Auto-loaded {os.path.basename(p)} "
                                  f"({len(songs)} tracks)")
                        break

                # Load existing progress
                prog = load_progress()
                self.card_migrated.set_value(str(prog["migrated_count"]))
                self.card_failed.set_value(str(prog["failed_rows"]))
                return
            except Exception as e:
                self._log(f"⚠️ Auth file exists but login failed: {e}")

        self.auth_indicator.configure(
            text="● Disconnected", text_color=BRAND_RED)
        self._log("⚠️ Not authenticated. Go to Settings → paste cURL.")

    def _authenticate(self):
        raw_curl = self.curl_textbox.get("1.0", "end").strip()
        if not raw_curl:
            self.auth_status_label.configure(
                text="Paste cURL first!", text_color=BRAND_RED)
            return

        parsed, error = parse_curl(raw_curl)
        if error:
            self.auth_status_label.configure(
                text=f"❌ {error}", text_color=BRAND_RED)
            return

        try:
            # Save headers
            with open(HEADERS_PATH, 'w', encoding='utf-8') as f:
                f.write(raw_curl)

            # Create oauth.json
            if os.path.exists(AUTH_JSON_PATH):
                os.remove(AUTH_JSON_PATH)
            setup_browser(AUTH_JSON_PATH, parsed)
            self.ytm = YTMusic(AUTH_JSON_PATH)

            self.auth_status_label.configure(
                text="✅ Authenticated!", text_color=BRAND_GREEN)
            self.auth_indicator.configure(
                text="● Connected", text_color=BRAND_GREEN)
            self._log("✅ Successfully authenticated with YouTube Music!")
        except Exception as e:
            self.auth_status_label.configure(
                text=f"❌ {e}", text_color=BRAND_RED)
            self._log(f"❌ Auth failed: {e}")

    # ── CSV ───────────────────────────────────────────────────────

    def _browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV Library File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=BASE_DIR
        )
        if path:
            self.csv_path = path
            songs = universal_csv_parser(path)
            self.songs = songs
            self.csv_label.configure(
                text=os.path.basename(path), text_color=BRAND_GREEN)
            self.card_total.set_value(str(len(songs)))
            self._log(f"📄 Loaded {os.path.basename(path)} "
                      f"({len(songs)} tracks)")

    # ── Migration ─────────────────────────────────────────────────

    def _start_migration(self):
        if not self.ytm:
            messagebox.showwarning(
                "Not Authenticated",
                "Go to Settings and authenticate first.")
            return
        if not self.songs:
            messagebox.showwarning(
                "No CSV",
                "Please select a CSV file with tracks to migrate.")
            return

        self.is_migrating = True
        self.stop_flag = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log("🚀 Migration started!")

        thread = threading.Thread(target=self._migration_worker, daemon=True)
        thread.start()

    def _stop_migration(self):
        self.stop_flag = True
        self._log("🛑 Stop requested...")

    def _migration_worker(self):
        songs = list(self.songs)
        if self.reverse_var.get():
            songs.reverse()

        is_smart = self.smart_var.get()
        is_dry_run = self.dryrun_var.get()

        # Determine destination
        target_playlist_id = None
        dest = self.dest_var.get()
        if dest == "new_playlist" and not is_dry_run:
            name = self.playlist_name_entry.get().strip() or "Migratify Playlist"
            try:
                target_playlist_id = self.ytm.create_playlist(
                    name, "Migrated via Migratify")
                self._safe_update(
                    lambda: self._log(f"✅ Created playlist: {name}"))
            except Exception as e:
                self._safe_update(
                    lambda: self._log(f"❌ Failed to create playlist: {e}"))
                self._migration_done()
                return
        elif dest == "existing" and not is_dry_run:
            name = self.playlist_name_entry.get().strip()
            try:
                playlists = self.ytm.get_library_playlists(limit=50)
                match = next(
                    (p for p in playlists
                     if p['title'].lower() == name.lower()), None)
                if match:
                    target_playlist_id = match['playlistId']
                else:
                    self._safe_update(
                        lambda: self._log(
                            f"❌ Playlist '{name}' not found. Using Liked."))
            except Exception as e:
                self._safe_update(
                    lambda: self._log(f"⚠️ Could not list playlists: {e}"))

        history_set = load_history()
        progress = load_progress()
        start = progress["processed_rows"]
        total = len(songs)

        if start >= total:
            self._safe_update(lambda: self._log("✅ Already completed!"))
            self._migration_done()
            return

        migrated = progress["migrated_count"]
        failed = progress["failed_rows"]

        for i in range(start, total):
            if self.stop_flag:
                break

            song = songs[i]
            query = f"{song['artist']} - {song['track']}".strip(" -")
            if not query:
                continue

            pct = (i - start + 1) / (total - start)
            self._safe_update(lambda p=pct, q=query, idx=i: self._update_progress(
                p, f"[{idx+1}/{total}] {q}"))

            try:
                results = self.ytm.search(query, filter="songs")
                vid = None

                if results:
                    if is_smart and song['target_sec']:
                        for r in results:
                            dur = get_duration_sec(r.get('duration'))
                            if dur and abs(dur - song['target_sec']) <= 90:
                                vid = r['videoId']
                                break
                        if not vid:
                            vid = results[0].get('videoId')
                    else:
                        vid = results[0].get('videoId')

                if vid:
                    if not is_dry_run and vid not in history_set:
                        if target_playlist_id:
                            self.ytm.add_playlist_items(
                                target_playlist_id, [vid])
                        else:
                            self.ytm.rate_song(vid, 'LIKE')
                        history_set.add(vid)
                    migrated += 1
                    self._safe_update(
                        lambda m=migrated: self.card_migrated.set_value(str(m)))
                else:
                    failed += 1
                    log_failed_song(i + 1, query, "Not found")
                    self._safe_update(
                        lambda f=failed: self.card_failed.set_value(str(f)))

            except Exception as e:
                err = str(e)
                if "401" in err or "Unauthorized" in err:
                    self._safe_update(
                        lambda: self._log(
                            "⚠️ SESSION EXPIRED! Re-authenticate in Settings."))
                    break
                failed += 1
                log_failed_song(i + 1, query, err)
                self._safe_update(
                    lambda f=failed: self.card_failed.set_value(str(f)))

            progress["processed_rows"] = i + 1
            progress["migrated_count"] = migrated
            progress["failed_rows"] = failed

            if i % 10 == 0:
                save_progress(progress)
                save_history(history_set)
                if not is_dry_run:
                    time.sleep(0.3)

        save_progress(progress)
        save_history(history_set)

        self._safe_update(lambda: self._log(
            f"📊 Done! Migrated: {migrated} | Failed: {failed} | "
            f"Total: {total}"))
        self._migration_done()

    def _update_progress(self, pct, label):
        self.progress_bar.set(pct)
        self.progress_label.configure(
            text=f"{int(pct * 100)}% complete")
        self.current_track_label.configure(text=label)

    def _migration_done(self):
        self.is_migrating = False
        self._safe_update(lambda: self.start_btn.configure(state="normal"))
        self._safe_update(lambda: self.stop_btn.configure(state="disabled"))
        self._safe_update(lambda: self.progress_label.configure(
            text="Migration complete"))

    # ── Batch ─────────────────────────────────────────────────────

    def _open_batch_folder(self):
        os.makedirs(BATCH_DIR, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(BATCH_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", BATCH_DIR])
        else:
            subprocess.Popen(["xdg-open", BATCH_DIR])
        self._batch_log_msg(f"📂 Opened folder: {BATCH_DIR}")

    def _start_batch(self):
        if not self.ytm:
            messagebox.showwarning("Not Authenticated",
                                   "Go to Settings first.")
            return

        os.makedirs(BATCH_DIR, exist_ok=True)
        csvs = [f for f in os.listdir(BATCH_DIR) if f.endswith('.csv')]
        if not csvs:
            messagebox.showinfo("Empty", "No CSVs found in csv_batch folder.")
            return

        self.batch_start_btn.configure(state="disabled")
        self._batch_log_msg(f"Found {len(csvs)} CSV files. Starting...")

        thread = threading.Thread(
            target=self._batch_worker, args=(csvs,), daemon=True)
        thread.start()

    def _batch_worker(self, csvs):
        is_smart = self.batch_smart_var.get()
        history_set = load_history()

        for file_idx, filename in enumerate(csvs):
            filepath = os.path.join(BATCH_DIR, filename)
            pl_name = filename[:-4]
            songs = universal_csv_parser(filepath)
            if not songs:
                continue

            self._safe_update(
                lambda n=pl_name, c=len(songs): self._batch_log_msg(
                    f"📁 [{file_idx+1}/{len(csvs)}] {n} — {c} tracks"))

            try:
                pl_id = self.ytm.create_playlist(
                    pl_name, "Migrated via Migratify")
            except Exception as e:
                self._safe_update(
                    lambda: self._batch_log_msg(f"❌ Create playlist failed: {e}"))
                continue

            time.sleep(1)

            for i, data in enumerate(songs):
                if self.stop_flag:
                    break

                query = f"{data['artist']} - {data['track']}".strip(" -")
                if not query:
                    continue

                pct = (file_idx + (i + 1) / len(songs)) / len(csvs)
                self._safe_update(
                    lambda p=pct: self.batch_progress_bar.set(p))
                self._safe_update(
                    lambda n=pl_name, idx=i, t=len(songs):
                        self.batch_progress_label.configure(
                            text=f"{n} — {idx+1}/{t}"))

                try:
                    res = self.ytm.search(query, filter="songs")
                    vid = None
                    if res:
                        if is_smart and data['target_sec']:
                            for r in res:
                                dur = get_duration_sec(r.get('duration'))
                                if (dur and
                                        abs(dur - data['target_sec']) <= 90):
                                    vid = r['videoId']
                                    break
                        if not vid and res[0].get('videoId'):
                            vid = res[0]['videoId']
                    if vid:
                        self.ytm.add_playlist_items(pl_id, [vid])
                        history_set.add(vid)
                    else:
                        log_failed_song(i + 1, query, "Not found")
                except Exception:
                    pass

                if i % 10 == 0:
                    save_history(history_set)
                    time.sleep(0.3)

            save_history(history_set)
            self._safe_update(
                lambda n=pl_name: self._batch_log_msg(f"✅ {n} — done!"))

        self._safe_update(
            lambda: self._batch_log_msg("🎉 Batch migration complete!"))
        self._safe_update(
            lambda: self.batch_start_btn.configure(state="normal"))

    # ── Fix Errors ────────────────────────────────────────────────

    def _load_failed_songs(self):
        # Clear previous
        for w in self.fix_scroll.winfo_children():
            w.destroy()

        if not os.path.exists(FAILED_CSV_PATH):
            ctk.CTkLabel(
                self.fix_scroll,
                text="✅ No failed songs! Nothing to fix.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14),
                text_color=BRAND_GREEN
            ).pack(padx=16, pady=24)
            return

        if not self.ytm:
            messagebox.showwarning("Not Authenticated",
                                   "Go to Settings first.")
            return

        failed = []
        with open(FAILED_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and len(row) > 1 and row[1] != "Query":
                    failed.append((row[0], row[1],
                                   row[2] if len(row) > 2 else ""))

        if not failed:
            ctk.CTkLabel(
                self.fix_scroll,
                text="✅ No failed songs!",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14),
                text_color=BRAND_GREEN
            ).pack(padx=16, pady=24)
            return

        self._log(f"🛠 Loading {len(failed)} failed songs for fixing...")

        # Load them in a thread to not block UI
        thread = threading.Thread(
            target=self._fix_search_worker, args=(failed,), daemon=True)
        thread.start()

    def _fix_search_worker(self, failed):
        for row_idx, query, err in failed:
            try:
                results = self.ytm.search(query, filter="songs")[:5]
            except Exception:
                results = []

            self._safe_update(
                lambda q=query, e=err, r=results, ri=row_idx:
                    self._render_fix_card(q, e, r, ri))
            time.sleep(0.5)

    def _render_fix_card(self, query, error, results, row_idx):
        card = ctk.CTkFrame(self.fix_scroll, fg_color=BRAND_CARD,
                            corner_radius=12)
        card.pack(padx=4, pady=6, fill="x")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(padx=12, pady=(10, 4), fill="x")

        ctk.CTkLabel(
            header, text=f"🔎 {query}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=BRAND_TEXT
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"({error})",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=BRAND_RED
        ).pack(side="right")

        if not results:
            ctk.CTkLabel(
                card, text="No results found",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=BRAND_DIM
            ).pack(padx=12, pady=(0, 10))
            return

        for i, res in enumerate(results):
            artist = ", ".join(
                [a['name'] for a in res.get('artists', [])]
            ) if res.get('artists') else 'Unknown'
            title = res.get('title', 'Unknown')
            dur = res.get('duration', '?:??')
            vid = res.get('videoId')

            if not vid:
                continue

            row = ctk.CTkFrame(card, fg_color=BRAND_SURFACE,
                               corner_radius=8)
            row.pack(padx=12, pady=2, fill="x")

            ctk.CTkLabel(
                row, text=f"{dur}  |  {artist} — {title}",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=BRAND_TEXT
            ).pack(side="left", padx=10, pady=6)

            ctk.CTkButton(
                row, text="✅ Pick", width=70, height=28,
                corner_radius=6, fg_color=BRAND_GREEN,
                text_color=BRAND_DARK,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                command=lambda v=vid, c=card, q=query: self._fix_pick(v, c, q)
            ).pack(side="right", padx=8, pady=4)

    def _fix_pick(self, video_id, card, query):
        if not self.ytm:
            return
        try:
            history = load_history()
            if video_id not in history:
                self.ytm.rate_song(video_id, 'LIKE')
                history.add(video_id)
                save_history(history)
            card.configure(fg_color="#0D2818")
            for w in card.winfo_children():
                w.destroy()
            ctk.CTkLabel(
                card, text=f"✅ Fixed: {query}",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=BRAND_GREEN
            ).pack(padx=12, pady=10)
            self._log(f"✅ Fixed: {query}")

            # Remove from failed CSV
            self._remove_from_failed(query)
        except Exception as e:
            self._log(f"❌ Fix failed for {query}: {e}")

    def _remove_from_failed(self, query):
        if not os.path.exists(FAILED_CSV_PATH):
            return
        remaining = []
        with open(FAILED_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and len(row) > 1 and row[1] != query:
                    remaining.append(row)

        if len(remaining) <= 1:  # only header or empty
            os.remove(FAILED_CSV_PATH)
        else:
            with open(FAILED_CSV_PATH, 'w', encoding='utf-8',
                      newline='') as f:
                writer = csv.writer(f)
                writer.writerows(remaining)

    # ── Resets ────────────────────────────────────────────────────

    def _reset_progress(self):
        if messagebox.askyesno("Reset Progress",
                               "This will reset migration progress. Continue?"):
            for p in [PROGRESS_PATH]:
                if os.path.exists(p):
                    os.remove(p)
            self.card_migrated.set_value("0")
            self.card_failed.set_value("0")
            self.progress_bar.set(0)
            self._log("🗑️ Progress reset.")

    def _reset_auth(self):
        if messagebox.askyesno("Reset Auth",
                               "This will require re-authentication."):
            for p in [AUTH_JSON_PATH, HEADERS_PATH]:
                if os.path.exists(p):
                    os.remove(p)
            self.ytm = None
            self.auth_indicator.configure(
                text="● Disconnected", text_color=BRAND_RED)
            self._log("🗑️ Auth reset. Paste new cURL in Settings.")

    def _reset_history(self):
        if messagebox.askyesno("Reset History",
                               "This will allow re-adding duplicate songs."):
            if os.path.exists(HISTORY_PATH):
                os.remove(HISTORY_PATH)
            self._log("🗑️ Duplicate history cleared.")

    # ── Thread-safe UI updates ────────────────────────────────────

    def _safe_update(self, func):
        """Schedule a function to run on the main thread."""
        self.after(0, func)


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = MigratifyApp()
    app.mainloop()

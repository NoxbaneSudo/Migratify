"""
Migratify GUI — Pro Max Edition
Built with CustomTkinter, FontAwesome Vector Icons, and Pillow Graphics Engine.
"""

import sys
import subprocess
import os

GUI_DEPS = ["customtkinter", "ytmusicapi", "colorama", "tqdm", "Pillow", "requests"]

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

import re
import csv
import json
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import urllib.request

import requests
from PIL import Image, ImageTk, ImageFilter, ImageDraw
import customtkinter as ctk
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup_browser

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

CSV_PATH = os.path.join(BASE_DIR, "library.csv")
HEADERS_PATH = os.path.join(BASE_DIR, "headers.txt")
AUTH_JSON_PATH = os.path.join(BASE_DIR, "oauth.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "progress.json")
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
FAILED_CSV_PATH = os.path.join(BASE_DIR, "failed_songs.csv")
BATCH_DIR = os.path.join(BASE_DIR, "csv_batch")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
FONT_PATH = os.path.join(ASSETS_DIR, "fa-solid.ttf")

# ─── Fonts & Icons ────────────────────────────────────────────────
FA_URL = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf"
if not os.path.exists(FONT_PATH):
    print("[Migratify GUI] Downloading vector icons...")
    try:
        urllib.request.urlretrieve(FA_URL, FONT_PATH)
    except Exception as e:
        print(f"Failed to download font: {e}")

if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)

ICON_HOME = "\uf015"
ICON_ROCKET = "\uf135"
ICON_BOXES = "\uf492"
ICON_WRENCH = "\uf0ad"
ICON_GEAR = "\uf013"
ICON_PLAY = "\uf04b"
ICON_STOP = "\uf04d"
ICON_MOON = "\uf186"
ICON_FILE = "\uf15c"

FONT_FAMILY = "Poppins"
ICON_FONT = "Font Awesome 6 Free Solid"

# ─── App Constants ────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

LOCALES = {
    "en": {
        "tab_dash": f"{ICON_HOME}  Dashboard", "tab_migrate": f"{ICON_ROCKET}  Migrate", 
        "tab_batch": f"{ICON_BOXES}  Batch", "tab_fix": f"{ICON_WRENCH}  Fix Errors", 
        "tab_settings": f"{ICON_GEAR}  Settings",
        "auth_title": "YouTube Music Auth", "auth_desc": "Paste your cURL (bash) request below.",
        "btn_auth": "Link Account", "btn_start": f"{ICON_PLAY}  START", "btn_stop": f"{ICON_STOP}  STOP", 
        "btn_browse": f"{ICON_FILE}  Browse CSV...", "dash_title": "Dashboard", "dash_sub": "Overview of your migration progress",
        "stat_mig": "Migrated", "stat_fail": "Failed", "stat_tot": "Total in CSV", "log_title": "Activity Log",
        "mig_title": "Single CSV Migration", "mig_sub": "Migrate from a single file",
        "opt_smart": "Smart Search (duration ±90s)", "opt_rev": "Reverse Order", "opt_dry": "Dry Run (simulation)",
        "dest_like": "Liked Songs", "dest_new": "New Playlist", "dest_exist": "Existing Playlist",
        "batch_title": "Batch Migration", "batch_sub": "Drop CSVs into csv_batch",
        "btn_batch_start": "Start Batch", "btn_batch_open": "Open Folder",
        "fix_title": "Fix Failed Songs", "fix_sub": "Manually pick the correct track",
        "btn_fix_load": "Load Errors", "btn_pick": "Pick", "set_title": "Settings", "set_sub": "App Preferences",
        "set_lang": "Language", "set_theme": "Theme", "set_bg": "Custom Background",
        "set_reset": "Reset Data", "btn_reset_prog": "Reset Progress", "btn_reset_auth": "Sign Out", "btn_reset_hist": "Clear History",
        "theme_coffee": "Coffee", "theme_dark": "Dark", "theme_light": "Light", "theme_asphalt": "Asphalt", "theme_nebula": "Nebula",
        "btn_load_bg": "Load Custom Image", "btn_clear_bg": "Clear Background",
        "eta_msg": "{pct}%  •  {eta}", "conn_yes": "Connected", "conn_no": "Disconnected",
        "msg_playlists": "Your Playlists:", "err_auth_first": "Authenticate in Migrate tab first."
    }
}

THEMES = {
    "coffee": {
        "accent": "#F4C9D6", "hover": "#DCC2C5", "dark": "#281914",
        "surface": "#200F07", "card": "#3E2723", "border": "#5C3A21",
        "text": "#FFF0F5", "dim": "#DCC2C5", "red": "#FF6B6B",
        "yellow": "#E9C46A", "cyan": "#A2D2FF", "green": "#00E676",
        "grad_top": "#3E2723", "grad_bot": "#200F07"
    },
    "dark": {
        "accent": "#3B82F6", "hover": "#2563EB", "dark": "#0F172A",
        "surface": "#1E293B", "card": "#0F172A", "border": "#334155",
        "text": "#F8FAFC", "dim": "#94A3B8", "red": "#EF4444",
        "yellow": "#F59E0B", "cyan": "#38BDF8", "green": "#10B981",
        "grad_top": "#1E293B", "grad_bot": "#0F172A"
    },
    "light": {
        "accent": "#2563EB", "hover": "#1D4ED8", "dark": "#F8FAFC",
        "surface": "#E2E8F0", "card": "#FFFFFF", "border": "#CBD5E1",
        "text": "#0F172A", "dim": "#64748B", "red": "#DC2626",
        "yellow": "#D97706", "cyan": "#0284C7", "green": "#059669",
        "grad_top": "#E2E8F0", "grad_bot": "#CBD5E1"
    },
    "asphalt": {
        "accent": "#efede3", "hover": "#e0ded4", "dark": "#302f2c",
        "surface": "#252422", "card": "#3A3935", "border": "#4F4E49",
        "text": "#F8FAFC", "dim": "#A3A199", "red": "#FF6B6B",
        "yellow": "#F59E0B", "cyan": "#38BDF8", "green": "#00E676",
        "grad_top": "#efede3", "grad_bot": "#302f2c"
    },
    "nebula": {
        "accent": "#c3b9e1", "hover": "#a59ecf", "dark": "#141026",
        "surface": "#1c1836", "card": "#2b2659", "border": "#3e3873",
        "text": "#f8f7ff", "dim": "#a59ecf", "red": "#FF6B6B",
        "yellow": "#F59E0B", "cyan": "#38BDF8", "green": "#00E676",
        "grad_top": "#141026", "grad_bot": "#6b63a6"
    }
}

from patch_migrate import universal_csv_parser, log_failed_song, parse_curl
import patch_migrate # ensure patched

# History routines
def load_history():
    if not os.path.exists(HISTORY_PATH): return set()
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception: return set()

def save_history(h):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(list(h), f, ensure_ascii=False, indent=2)

def load_progress():
    if not os.path.exists(PROGRESS_PATH):
        return {"processed_rows": 0, "migrated_count": 0, "failed_rows": 0}
    try:
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"processed_rows": 0, "migrated_count": 0, "failed_rows": 0}

def save_progress(p):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

# ─── UI Components ────────────────────────────────────────────────
class GlowButton(ctk.CTkButton):
    def __init__(self, master, current_theme, **kwargs):
        kwargs.setdefault("corner_radius", 22)
        kwargs.setdefault("height", 44)
        kwargs.setdefault("font", ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"))
        kwargs.setdefault("fg_color", THEMES[current_theme]["accent"])
        text_color = "#3E2723" if current_theme == "coffee" else THEMES[current_theme]["dark"]
        if current_theme == "asphalt": text_color = THEMES[current_theme]["dark"]
        kwargs.setdefault("text_color", text_color)
        kwargs.setdefault("hover_color", THEMES[current_theme]["hover"])
        super().__init__(master, **kwargs)

class StatusCard(ctk.CTkFrame):
    def __init__(self, master, label, current_theme, value="0", color_key="accent", **kwargs):
        c_th = THEMES[current_theme]
        # Make cards semi-transparent (a workaround is putting them on a surface frame) but we use solid for now
        super().__init__(master, fg_color=c_th["card"], corner_radius=20, border_width=1, border_color=c_th["border"], **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=c_th["dim"])
        self.label.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")
        self.value_label = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"), text_color=c_th[color_key])
        self.value_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")
    def set_value(self, val):
        self.value_label.configure(text=str(val))

class MigratifyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Migratify — Premium App")
        self.geometry("960x680")
        self.minsize(800, 600)

        # Settings
        self.settings = {"lang": "en", "theme": "coffee", "bg_image": "", "bg_blur": 15}
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r") as f:
                    self.settings.update(json.load(f))
            except Exception: pass

        self.lang = self.settings["lang"]
        self.theme = self.settings["theme"]
        
        self.ytm = None
        self.csv_path = None
        self.songs = []
        self.is_migrating, self.stop_flag = False, False
        self.pages, self.nav_buttons = {}, {}

        # The Backing Canvas for Image/Gradient
        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_app()
        self._check_auth_status()
        self.bind("<Configure>", self._on_resize)
        self.after(50, self._render_background)

    def _save_settings(self):
        with open(SETTINGS_PATH, "w") as f:
            json.dump(self.settings, f)

    def tr(self, key): return LOCALES[self.lang].get(key, key)
    def th(self, key): return THEMES[self.theme][key]

    # ── Background Engine ───────────────────────────────────────
    def _on_resize(self, event):
        # Debounce the render to save CPU
        if getattr(self, "_resize_timer", None):
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(300, self._render_background)

    def _render_background(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 100 or h < 100: return

        if self.settings.get("bg_image") and os.path.exists(self.settings["bg_image"]):
            # Render Custom Blurred Image
            try:
                img = Image.open(self.settings["bg_image"]).convert("RGB")
                # Resize aspect-fill
                img_ratio = img.width / img.height
                scr_ratio = w / h
                if scr_ratio > img_ratio:
                    new_w, new_h = w, int(w / img_ratio)
                else:
                    new_w, new_h = int(h * img_ratio), h
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                # Crop to center
                left = (new_w - w)/2
                top = (new_h - h)/2
                img = img.crop((left, top, left+w, top+h))
                
                blur_val = self.settings.get("bg_blur", 15)
                if blur_val > 0:
                    img = img.filter(ImageFilter.GaussianBlur(radius=blur_val))
                
                # Darken slightly for readability
                enhancer = Image.eval(img, lambda p: p * 0.7)
                
                ctk_img = ctk.CTkImage(light_image=enhancer, dark_image=enhancer, size=(w, h))
                self.bg_label.configure(image=ctk_img)
                return
            except Exception as e:
                print(f"BG Load Error: {e}")
        
        # Render Gradient if supported (e.g. Asphalt)
        if "grad_top" in THEMES[self.theme]:
            img = Image.new("RGB", (w, h))
            draw = ImageDraw.Draw(img)
            c1_hex = THEMES[self.theme]["grad_top"].lstrip('#')
            c2_hex = THEMES[self.theme]["grad_bot"].lstrip('#')
            c1 = tuple(int(c1_hex[i:i+2], 16) for i in (0, 2, 4))
            c2 = tuple(int(c2_hex[i:i+2], 16) for i in (0, 2, 4))
            for y in range(h):
                r = int(c1[0] + (c2[0] - c1[0]) * y / h)
                g = int(c1[1] + (c2[1] - c1[1]) * y / h)
                b = int(c1[2] + (c2[2] - c1[2]) * y / h)
                draw.line([(0, y), (w, y)], fill=(r,g,b))
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            self.bg_label.configure(image=ctk_img)
        else:
            self.bg_label.configure(image=None, fg_color=self.th("dark"))

    def _apply_theme_setting(self, val):
        t_id_map = {
            "Coffee": "coffee", "Dark": "dark", "Light": "light", "Asphalt": "asphalt", "Nebula": "nebula"
        }
        self.theme = t_id_map[val]
        self.settings["theme"] = self.theme
        self._save_settings()
        self._build_app()
        self._render_background()

    def _load_custom_bg(self):
        filename = filedialog.askopenfilename(title="Select Background Image", filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if filename:
            self.settings["bg_image"] = filename
            self._save_settings()
            self._render_background()

    def _clear_custom_bg(self):
        self.settings["bg_image"] = ""
        self._save_settings()
        self._render_background()

    def _build_app(self):
        # We handle backgrounds manually
        self.configure(fg_color=self.th("dark"))
        for widget in self.winfo_children(): widget.destroy()

        self.grid_rowconfigure(0, weight=0) # Navbar
        self.grid_rowconfigure(1, weight=0) # Global Bar (Top Launcher Style)
        self.grid_rowconfigure(2, weight=1) # Main Area
        self.grid_columnconfigure(0, weight=1)

        # ── Navbar ───────────────────────────────────────────────
        nav_bg = self.th("surface")
        navbar = ctk.CTkFrame(self, height=54, fg_color=nav_bg, corner_radius=0, border_color=self.th("border"), border_width=1)
        navbar.grid(row=0, column=0, sticky="ew")
        navbar.grid_columnconfigure(1, weight=1)

        # Logo
        logo_txt = "Migratify"
        logo = ctk.CTkLabel(navbar, text=logo_txt, font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=self.th("accent"))
        logo.pack(side="left", padx=(24, 0), pady=12)

        nav_items = [
            (self.tr("tab_dash"), "dashboard"),
            (self.tr("tab_migrate"), "migrate"),
            (self.tr("tab_batch"), "batch"),
            (self.tr("tab_fix"), "fix"),
            (self.tr("tab_settings"), "settings")
        ]
        
        btn_area = ctk.CTkFrame(navbar, fg_color="transparent")
        btn_area.pack(side="left", fill="y", padx=(20, 0))

        for label, key in nav_items:
            btn = ctk.CTkButton(
                btn_area, text=label, width=1, height=36, corner_radius=18,
                fg_color="transparent", text_color=self.th("text"), hover_color=self.th("card"),
                font=ctk.CTkFont(family=ICON_FONT, size=13),
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", padx=6, pady=9)
            self.nav_buttons[key] = btn

        self.auth_indicator = ctk.CTkLabel(navbar, text=self.tr("conn_no"), font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=self.th("red"))
        self.auth_indicator.pack(side="right", padx=24, pady=12)

        # ── Global Action Bar (TOP) ────────────────────────────────
        self.action_bar = ctk.CTkFrame(self, height=84, fg_color=self.th("card"), corner_radius=0, border_width=1, border_color=self.th("border"))
        self.action_bar.grid(row=1, column=0, sticky="ew")
        
        self.action_inner = ctk.CTkFrame(self.action_bar, fg_color="transparent")
        self.action_inner.pack(fill="x", padx=24, pady=12)
        self.action_inner.grid_columnconfigure(1, weight=1)

        self.action_start_btn = GlowButton(self.action_inner, current_theme=self.theme, text=self.tr("btn_start"), width=160, font=ctk.CTkFont(family=ICON_FONT, size=14, weight="bold"), command=self._start_from_action_bar)
        self.action_start_btn.grid(row=0, column=0, sticky="w")

        self.action_stop_btn = ctk.CTkButton(self.action_inner, text=self.tr("btn_stop"), width=160, height=44, corner_radius=22, fg_color=self.th("red"), hover_color=self.th("hover"), text_color="white", font=ctk.CTkFont(family=ICON_FONT, size=14, weight="bold"), command=self._stop_migration)
        
        self.prog_area = ctk.CTkFrame(self.action_inner, fg_color="transparent")
        self.prog_area.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.prog_area.grid_columnconfigure(0, weight=1)
        
        self.global_prog_label = ctk.CTkLabel(self.prog_area, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("dim"))
        self.global_prog_label.grid(row=0, column=0, sticky="w")
        
        self.global_prog_bar = ctk.CTkProgressBar(self.prog_area, progress_color=self.th("accent"), fg_color=self.th("surface"), height=10, corner_radius=5)
        self.global_prog_bar.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.global_prog_bar.set(0)

        # ── Main Content Container ───────────────────────────────
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=2, column=0, sticky="nswe")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self._build_dashboard_page()
        self._build_migrate_page()
        self._build_batch_page()
        self._build_fix_page()
        self._build_settings_page()

        self._switch_tab("dashboard")

    def _switch_tab(self, tab_name):
        self.current_tab = tab_name
        
        if tab_name in ["dashboard", "settings"]: self.action_bar.grid_remove()
        else: self.action_bar.grid()

        for key, btn in self.nav_buttons.items():
            if key == tab_name: btn.configure(fg_color=self.th("surface"), text_color=self.th("accent"))
            else: btn.configure(fg_color="transparent", text_color=self.th("text"))

        for key, page in self.pages.items():
            if key != tab_name:
                try: page.place_forget()
                except: pass

        self.pages[tab_name].place(relx=0.08, rely=0, relwidth=1, relheight=1)
        self._animate_slide(tab_name, 0.08)

    def _animate_slide(self, tab_name, current_relx):
        if current_relx > 0.002:
            new_relx = current_relx * 0.7 
            self.pages[tab_name].place(relx=new_relx, rely=0, relwidth=1, relheight=1)
            self.after(16, self._animate_slide, tab_name, new_relx)
        else:
            self.pages[tab_name].place(relx=0, rely=0, relwidth=1, relheight=1)

    # ── Pages ─────────────────────────────────────────────────────

    def _build_dashboard_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        page.grid_columnconfigure((0, 1, 2), weight=1)
        self.pages["dashboard"] = page

        ctk.CTkLabel(page, text=self.tr("dash_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"), text_color=self.th("text")).grid(row=0, column=0, columnspan=3, padx=24, pady=(24, 4), sticky="w")
        ctk.CTkLabel(page, text=self.tr("dash_sub"), font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=self.th("dim")).grid(row=1, column=0, columnspan=3, padx=24, pady=(0, 16), sticky="w")

        self.card_migrated = StatusCard(page, self.tr("stat_mig"), current_theme=self.theme, value="0", color_key="accent")
        self.card_migrated.grid(row=2, column=0, padx=(24, 8), pady=8, sticky="nswe")

        self.card_failed = StatusCard(page, self.tr("stat_fail"), current_theme=self.theme, value="0", color_key="red")
        self.card_failed.grid(row=2, column=1, padx=8, pady=8, sticky="nswe")

        self.card_total = StatusCard(page, self.tr("stat_tot"), current_theme=self.theme, value="—", color_key="cyan")
        self.card_total.grid(row=2, column=2, padx=(8, 24), pady=8, sticky="nswe")

        ctk.CTkLabel(page, text=self.tr("log_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"), text_color=self.th("text")).grid(row=3, column=0, columnspan=3, padx=24, pady=(20, 4), sticky="w")
        
        split = ctk.CTkFrame(page, fg_color="transparent")
        split.grid(row=4, column=0, columnspan=3, padx=24, pady=(0, 24), sticky="nswe")
        split.grid_columnconfigure(0, weight=2)
        split.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(4, weight=1)

        self.log_box = ctk.CTkTextbox(split, fg_color=self.th("card"), text_color=self.th("text"), font=ctk.CTkFont(family="Consolas", size=12), corner_radius=20, border_width=1, border_color=self.th("border"), state="disabled")
        self.log_box.grid(row=0, column=0, sticky="nswe", padx=(0, 8))

        self.playlist_box = ctk.CTkTextbox(split, fg_color=self.th("card"), text_color=self.th("accent"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), corner_radius=20, border_width=1, border_color=self.th("border"), state="disabled")
        self.playlist_box.grid(row=0, column=1, sticky="nswe", padx=(8, 0))

    def _build_migrate_page(self):
        page = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.pages["migrate"] = page

        auth_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        auth_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(auth_card, text=self.tr("auth_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("text")).pack(padx=16, pady=(12, 4), anchor="w")
        ctk.CTkLabel(auth_card, text=self.tr("auth_desc"), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=self.th("dim"), justify="left").pack(padx=16, pady=(0, 8), anchor="w")

        self.curl_textbox = ctk.CTkTextbox(auth_card, height=100, fg_color=self.th("surface"), text_color=self.th("text"), font=ctk.CTkFont(family="Consolas", size=11), corner_radius=12, border_width=1, border_color=self.th("border"))
        self.curl_textbox.pack(padx=16, pady=(0, 8), fill="x")

        btn_row = ctk.CTkFrame(auth_card, fg_color="transparent")
        btn_row.pack(padx=16, pady=(0, 12), fill="x")
        GlowButton(btn_row, text=self.tr("btn_auth"), width=180, current_theme=self.theme, command=self._authenticate).pack(side="left")
        self.auth_status_label = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("dim"))
        self.auth_status_label.pack(side="left", padx=12)

        csv_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        csv_card.pack(padx=24, pady=8, fill="x")

        file_row = ctk.CTkFrame(csv_card, fg_color="transparent")
        file_row.pack(padx=16, pady=16, fill="x")
        self.csv_label = ctk.CTkLabel(file_row, text="No CSV selected", font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("dim"))
        self.csv_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(file_row, text=self.tr("btn_browse"), width=140, height=36, corner_radius=18, fg_color=self.th("border"), hover_color=self.th("surface"), text_color=self.th("text"), font=ctk.CTkFont(family=ICON_FONT, size=13), command=self._browse_csv).pack(side="right")

        opts_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        opts_card.pack(padx=24, pady=8, fill="x")
        
        self.smart_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(opts_card, text=self.tr("opt_smart"), variable=self.smart_var, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), progress_color=self.th("accent")).pack(padx=16, pady=12, anchor="w")
        self.reverse_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(opts_card, text=self.tr("opt_rev"), variable=self.reverse_var, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), progress_color=self.th("accent")).pack(padx=16, pady=(0, 12), anchor="w")
        self.dryrun_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(opts_card, text=self.tr("opt_dry"), variable=self.dryrun_var, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), progress_color=self.th("yellow")).pack(padx=16, pady=(0, 12), anchor="w")

        dest_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        dest_card.pack(padx=24, pady=8, fill="x", side="bottom")

        self.dest_var = ctk.StringVar(value="liked")
        ctk.CTkRadioButton(dest_card, text=self.tr("dest_like"), variable=self.dest_var, value="liked", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), fg_color=self.th("accent"), hover_color=self.th("hover")).pack(padx=16, pady=(16,4), anchor="w")
        ctk.CTkRadioButton(dest_card, text=self.tr("dest_new"), variable=self.dest_var, value="new_playlist", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), fg_color=self.th("accent"), hover_color=self.th("hover")).pack(padx=16, pady=4, anchor="w")
        ctk.CTkRadioButton(dest_card, text=self.tr("dest_exist"), variable=self.dest_var, value="existing", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), fg_color=self.th("accent"), hover_color=self.th("hover")).pack(padx=16, pady=(4, 4), anchor="w")

        self.playlist_name_entry = ctk.CTkEntry(dest_card, placeholder_text="Playlist name...", font=ctk.CTkFont(family=FONT_FAMILY, size=12), fg_color=self.th("surface"), border_color=self.th("border"), corner_radius=12, height=36)
        self.playlist_name_entry.pack(padx=16, pady=(4, 16), fill="x")

    def _build_batch_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages["batch"] = page

        ctk.CTkLabel(page, text=self.tr("batch_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"), text_color=self.th("text")).grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        ctk.CTkLabel(page, text=self.tr("batch_sub"), font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=self.th("dim")).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        info_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        info_card.grid(row=2, column=0, padx=24, pady=8, sticky="we")

        self.batch_smart_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(info_card, text=self.tr("opt_smart"), variable=self.batch_smart_var, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text"), progress_color=self.th("accent")).pack(padx=16, pady=16, anchor="w")

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=24, pady=8, sticky="we")

        ctk.CTkButton(btn_row, text=self.tr("btn_batch_open"), width=160, height=44, corner_radius=22, fg_color=self.th("border"), hover_color=self.th("surface"), text_color=self.th("text"), font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), command=self._open_batch_folder).pack(side="left")

        self.batch_log = ctk.CTkTextbox(page, fg_color=self.th("surface"), text_color=self.th("text"), font=ctk.CTkFont(family="Consolas", size=12), corner_radius=20, border_width=1, border_color=self.th("border"), state="disabled")
        self.batch_log.grid(row=6, column=0, padx=24, pady=(16, 24), sticky="nswe")
        page.grid_rowconfigure(6, weight=1)

    def _build_fix_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages["fix"] = page

        ctk.CTkLabel(page, text=self.tr("fix_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"), text_color=self.th("text")).grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        ctk.CTkLabel(page, text=self.tr("fix_sub"), font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=self.th("dim")).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        GlowButton(page, text=self.tr("btn_fix_load"), width=220, current_theme=self.theme, command=self._load_failed_songs).grid(row=2, column=0, padx=24, pady=8, sticky="w")

        self.fix_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.fix_scroll.grid(row=3, column=0, padx=24, pady=8, sticky="nswe")
        page.grid_rowconfigure(3, weight=1)

    def _build_settings_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["settings"] = page
        
        ctk.CTkLabel(page, text=self.tr("set_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"), text_color=self.th("text")).pack(padx=24, pady=(24, 4), anchor="w")
        ctk.CTkLabel(page, text=self.tr("set_sub"), font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=self.th("dim")).pack(padx=24, pady=(0, 16), anchor="w")

        # Theme Section
        theme_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        theme_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(theme_card, text=self.tr("set_theme"), font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("text")).pack(padx=16, pady=(12, 8), anchor="w")
        
        t_vals = [self.tr("theme_coffee"), self.tr("theme_dark"), self.tr("theme_light"), self.tr("theme_asphalt"), self.tr("theme_nebula")]
        t_id_rev = {"coffee": self.tr("theme_coffee"), "dark": self.tr("theme_dark"), "light": self.tr("theme_light"), "asphalt": self.tr("theme_asphalt"), "nebula": self.tr("theme_nebula")}
        self.theme_var = ctk.StringVar(value=t_id_rev.get(self.theme, self.tr("theme_coffee")))
        
        theme_opt = ctk.CTkOptionMenu(theme_card, variable=self.theme_var, values=t_vals, fg_color=self.th("surface"), button_color=self.th("border"), button_hover_color=self.th("hover"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12), command=self._apply_theme_setting)
        theme_opt.pack(padx=16, pady=(0, 16), anchor="w")

        # Reset Section
        reset_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        reset_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(reset_card, text=self.tr("set_reset"), font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("text")).pack(padx=16, pady=(12, 8), anchor="w")
        # Custom Background
        bg_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        bg_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(bg_card, text=self.tr("set_bg"), font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("text")).pack(padx=16, pady=(12, 8), anchor="w")
        
        bg_btns = ctk.CTkFrame(bg_card, fg_color="transparent")
        bg_btns.pack(padx=16, pady=(0, 16), fill="x")
        ctk.CTkButton(bg_btns, text=self.tr("btn_load_bg"), width=160, height=36, corner_radius=18, fg_color=self.th("accent"), hover_color=self.th("hover"), text_color=self.th("dark"), font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), command=self._load_custom_bg).pack(side="left", padx=(0, 12))
        
        if self.settings.get("bg_image"):
            ctk.CTkButton(bg_btns, text=self.tr("btn_clear_bg"), width=160, height=36, corner_radius=18, fg_color=self.th("border"), hover_color=self.th("red"), text_color=self.th("text"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), command=self._clear_custom_bg).pack(side="left")

        # Reset Section
        reset_card = ctk.CTkFrame(page, fg_color=self.th("card"), corner_radius=20, border_width=1, border_color=self.th("border"))
        reset_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(reset_card, text=self.tr("set_reset"), font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=self.th("text")).pack(padx=16, pady=(12, 8), anchor="w")
        
        btns = ctk.CTkFrame(reset_card, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 16), fill="x")
        
        ctk.CTkButton(btns, text=self.tr("btn_reset_prog"), width=140, height=36, corner_radius=18, fg_color=self.th("border"), hover_color=self.th("red"), text_color=self.th("text"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), command=self._reset_progress).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text=self.tr("btn_reset_auth"), width=140, height=36, corner_radius=18, fg_color=self.th("border"), hover_color=self.th("red"), text_color=self.th("text"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), command=self._reset_auth).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text=self.tr("btn_reset_hist"), width=140, height=36, corner_radius=18, fg_color=self.th("border"), hover_color=self.th("red"), text_color=self.th("text"), font=ctk.CTkFont(family=FONT_FAMILY, size=12), command=self._reset_history).pack(side="left")

    # ── Logic ─────────────────────────────────────────────────────

    def _browse_csv(self):
        filename = filedialog.askopenfilename(title="Select Library CSV", filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.csv_path = filename
            self.csv_label.configure(text=os.path.basename(filename), text_color=self.th("text"))

    def _open_batch_folder(self):
        os.makedirs(BATCH_DIR, exist_ok=True)
        import platform
        system = platform.system()
        if system == "Windows": os.startfile(BATCH_DIR)
        elif system == "Darwin": subprocess.Popen(["open", BATCH_DIR])
        else: subprocess.Popen(["xdg-open", BATCH_DIR])

    def _log_msg(self, msg, box=None):
        def _append():
            target = box if box else self.log_box
            target.configure(state="normal")
            target.insert("end", msg + "\n")
            target.see("end")
            target.configure(state="disabled")
        self.after(0, _append)

    def _check_auth_status(self):
        if os.path.exists(AUTH_JSON_PATH):
            try:
                self.ytm = YTMusic(AUTH_JSON_PATH)
                self.auth_indicator.configure(text=self.tr("conn_yes"), text_color=self.th("green"))
                threading.Thread(target=self._load_playlists, daemon=True).start()
            except Exception as e:
                self.ytm = None
                self.auth_indicator.configure(text=self.tr("conn_no"), text_color=self.th("red"))
        else:
            self.ytm = None
            self.auth_indicator.configure(text=self.tr("conn_no"), text_color=self.th("red"))
            self._update_playlists_box(self.tr("conn_no"))

    def _load_playlists(self):
        if not self.ytm: return
        try:
            pl = self.ytm.get_library_playlists(limit=15)
            text = self.tr("msg_playlists") + "\n\n"
            for p in pl:
                text += f"• {p.get('title', 'Unknown')} ({p.get('count', '?')})\n"
            self._update_playlists_box(text)
        except Exception:
            self._update_playlists_box("Error loading playlists.")

    def _update_playlists_box(self, text):
        def _set():
            self.playlist_box.configure(state="normal")
            self.playlist_box.delete("1.0", "end")
            self.playlist_box.insert("end", text)
            self.playlist_box.configure(state="disabled")
        self.after(0, _set)

    def _authenticate(self):
        raw_curl = self.curl_textbox.get("1.0", "end").strip()
        if not raw_curl:
            messagebox.showwarning("Warning", "Please paste the cURL command.")
            return

        headers_raw, err = parse_curl(raw_curl)
        if err:
            self.auth_status_label.configure(text=err, text_color=self.th("red"))
            return

        with open(HEADERS_PATH, "w", encoding="utf-8") as f: f.write(headers_raw)

        try:
            setup_browser(HEADERS_PATH, AUTH_JSON_PATH)
            self.ytm = YTMusic(AUTH_JSON_PATH)
            self.auth_status_label.configure(text="Authentication successful!", text_color=self.th("green"))
            self._check_auth_status()
            if os.path.exists(HEADERS_PATH): os.remove(HEADERS_PATH)
        except Exception as e:
            self.auth_status_label.configure(text=f"Failed", text_color=self.th("red"))
            self.ytm = None
            self._check_auth_status()

    def _reset_progress(self):
        if messagebox.askyesno("Confirm", "Reset progress and failed songs?"):
            for p in [PROGRESS_PATH, FAILED_CSV_PATH]:
                if os.path.exists(p): os.remove(p)
            self.card_migrated.set_value("0")
            self.card_failed.set_value("0")
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            self.log_box.configure(state="disabled")
            self.global_prog_bar.set(0)
            self.global_prog_label.configure(text="")

    def _reset_auth(self):
        if messagebox.askyesno("Confirm", "Log out of YouTube Music?"):
            for p in [AUTH_JSON_PATH, HEADERS_PATH]:
                if os.path.exists(p): os.remove(p)
            self._check_auth_status()
            self._update_playlists_box("")
            self.ytm = None

    def _reset_history(self):
        if messagebox.askyesno("Confirm", "Clear migration history (allows duplicates)?"):
            if os.path.exists(HISTORY_PATH): os.remove(HISTORY_PATH)

    def _start_from_action_bar(self):
        if self.current_tab == "batch": self._start_batch_migration()
        else: self._start_migration()

    def _animate_prog_bar(self, target_val, current_val=None):
        if current_val is None: current_val = self.global_prog_bar.get()
        diff = target_val - current_val
        if abs(diff) < 0.01:
            self.global_prog_bar.set(target_val)
            return
        new_val = current_val + (diff * 0.2)
        self.global_prog_bar.set(new_val)
        self.after(20, self._animate_prog_bar, target_val, new_val)

    def _update_ui_progress(self, current, total, migrated, failed, start_time):
        ratio = current / total if total > 0 else 0
        self._animate_prog_bar(ratio)
        self.card_migrated.set_value(migrated)
        self.card_failed.set_value(failed)
        elapsed = time.time() - start_time
        if ratio > 0.01:
            total_est = elapsed / ratio
            eta = max(0, total_est - elapsed)
            m, s = divmod(int(eta), 60)
            eta_str = f"{m}m {s}s"
        else: eta_str = "..."
        msg = self.tr("eta_msg").format(eta=eta_str, pct=int(ratio*100))
        self.global_prog_label.configure(text=msg)

    def _start_migration(self):
        if not self.ytm:
            messagebox.showwarning("Auth Error", self.tr("err_auth_first"))
            return
        if not self.csv_path:
            messagebox.showwarning("Error", "Please select a CSV file first.")
            return

        self.songs = universal_csv_parser(self.csv_path)
        if not self.songs:
            messagebox.showerror("Error", "No tracks found in CSV.")
            return

        if self.reverse_var.get(): self.songs.reverse()

        self.is_migrating, self.stop_flag = True, False
        
        self.action_start_btn.grid_forget()
        self.action_stop_btn.grid(row=0, column=0, sticky="w")
        self.card_total.set_value(len(self.songs))
        
        target_dest = self.dest_var.get()
        new_name = self.playlist_name_entry.get().strip()
        pl_id = None

        if target_dest == "new_playlist":
            try: pl_id = self.ytm.create_playlist(new_name, "Imported from Migratify"); self._log_msg(f"Created playlist")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create playlist: {e}")
                self._stop_migration(); return
        elif target_dest == "existing":
            messagebox.showinfo("Wait", "Not supported.")
            self._stop_migration(); return

        kwargs = {"songs": self.songs, "playlist_id": pl_id, "smart": self.smart_var.get(), "dry_run": self.dryrun_var.get(), "target_box": self.log_box}
        threading.Thread(target=self._worker, kwargs=kwargs, daemon=True).start()

    def _stop_migration(self):
        self.stop_flag = True
        self.is_migrating = False
        self.action_stop_btn.grid_forget()
        self.action_start_btn.grid(row=0, column=0, sticky="w")

    def _worker(self, songs, playlist_id, smart, dry_run, target_box):
        history, progress = load_history(), load_progress()
        total, start_t = len(songs), time.time()
        for idx, song in enumerate(songs):
            if self.stop_flag: break
            q = f"{song['track']} {song['artist']}".strip()
            self._log_msg(f"[{idx+1}/{total}] Searching: {q}", target_box)
            try:
                results = self.ytm.search(q, filter="songs")
                if not results or not results[0]['videoId']:
                    self._log_msg("  -> Not found.", target_box)
                    progress["failed_rows"] += 1
                    log_failed_song(idx+1, q, "Not found")
                    continue
                video_id = results[0]['videoId']
                if q in history:
                    progress["processed_rows"] += 1; continue
                if not dry_run:
                    if playlist_id: self.ytm.add_playlist_items(playlist_id, [video_id])
                    else: self.ytm.rate_song(video_id, "LIKE")
                    history.add(q)
                self._log_msg(f"  -> Added: {results[0].get('title', video_id)}", target_box)
                progress["migrated_count"] += 1; progress["processed_rows"] += 1
            except Exception as e:
                self._log_msg(f"  -> Error: {e}", target_box)
                progress["failed_rows"] += 1; log_failed_song(idx+1, q, str(e))
            save_history(history); save_progress(progress)
            self.after(0, self._update_ui_progress, progress["processed_rows"], total, progress["migrated_count"], progress["failed_rows"], start_t)
            time.sleep(0.5)
        self.after(0, self._stop_migration)
        self._log_msg("Migration finished or stopped.", target_box)

    def _start_batch_migration(self):
        if not self.ytm: return
        os.makedirs(BATCH_DIR, exist_ok=True)
        files = [f for f in os.listdir(BATCH_DIR) if f.lower().endswith(".csv")]
        if not files: return
        self.is_migrating, self.stop_flag = True, False
        self.action_start_btn.pack_forget()
        self.action_stop_btn.pack(side="left", padx=24, pady=14)
        threading.Thread(target=self._batch_worker, args=(files,), daemon=True).start()
        
    def _batch_worker(self, files):
        start_t = time.time()
        for i, fname in enumerate(files):
            if self.stop_flag: break
            p = os.path.join(BATCH_DIR, fname)
            songs = universal_csv_parser(p)
            if not songs: continue
            pl_name = fname.rsplit(".", 1)[0]
            try: pl_id = self.ytm.create_playlist(pl_name, "Batch"); self._worker(songs, pl_id, self.batch_smart_var.get(), False, self.batch_log)
            except Exception: continue
        self.after(0, self._stop_migration)

    def _load_failed_songs(self):
        if not os.path.exists(FAILED_CSV_PATH): return
        for w in self.fix_scroll.winfo_children(): w.destroy()
        with open(FAILED_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for i, row in enumerate(reader):
                if len(row) >= 2:
                    q = row[1]
                    f = ctk.CTkFrame(self.fix_scroll, fg_color=self.th("card"), corner_radius=12, border_width=1, border_color=self.th("border"))
                    f.pack(fill="x", pady=4, padx=4)
                    ctk.CTkLabel(f, text=f"{q}", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=self.th("text")).pack(side="left", padx=12, pady=12)

if __name__ == "__main__":
    app = MigratifyApp()
    app.mainloop()


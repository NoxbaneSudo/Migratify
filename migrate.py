# === Auto-install dependencies ===
import sys
import subprocess

REQUIRED = ["ytmusicapi", "colorama", "tqdm"]

def _ensure_deps():
    import importlib
    missing = []
    pkg_map = {"ytmusicapi": "ytmusicapi", "colorama": "colorama"}
    for pkg in REQUIRED:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg_map[pkg])
    if missing:
        print(f"[Migratify] Missing packages: {', '.join(missing)}. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("[Migratify] Done! Restarting...\n")
        # Re-exec so fresh imports are available
        import os
        os.execv(sys.executable, [sys.executable] + sys.argv)

_ensure_deps()
# === End auto-install ===

import csv
import os
import time
import json
import re
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup_browser
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "library.csv") # Renamed generically
HEADERS_PATH = os.path.join(BASE_DIR, "headers.txt")
AUTH_JSON_PATH = os.path.join(BASE_DIR, "oauth.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "progress.json")
FAILED_CSV_PATH = os.path.join(BASE_DIR, "failed_songs.csv")
# LOGS_PATH removed

def log_to_file(message):
    pass

LOGO = fr"""{Fore.GREEN}{Style.BRIGHT}
  __  __ _                 _   _  __       
 |  \/  (_)               | | (_)/ _|      
 | \  / |_  __ _ _ __ __ _| |_ _| |_ _   _ 
 | |\/| | |/ _` | '__/ _` | __| |  _| | | |
 | |  | | | (_| | | | (_| | |_| | | | |_| |
 |_|  |_|_|\__, |_|  \__,_|\__|_|_|  \__, |
            __/ |                     __/ |
           |___/                     |___/ 
{Fore.GREEN}       By NoxbaneSudo  {Style.RESET_ALL}
"""

def get_language():
    # Animated logo
    os.system('cls' if os.name == 'nt' else 'clear')
    for line in LOGO.split("\n"):
        for char in line:
            print(char, end='', flush=True)
            time.sleep(0.002)
        print()
    
    print("\nChoose your language / Выберите язык:")
    print("1. English")
    print("2. Русский")
    choice = input("> ").strip()
    return 'ru' if choice == '2' else 'en'

LANG_DATA = {
    "en": {
        "file_not_found": f"{Fore.RED}❌ Universal CSV file not found:",
        "put_csv": f"{Fore.YELLOW}Please place 'library.csv' (Exported from any service via Soundiiz/TuneMyMusic) into the script folder.",
        "headers_not_found": f"{Fore.RED}❌ Headers file not found:",
        "headers_ins": "1. Open YouTube Music, perform a search, and copy the request as 'cURL (bash)'.\n2. Create a 'headers.txt' file and paste the copied text.",
        "setup_auth": f"{Fore.CYAN}🔧 Initializing authorization...",
        "auth_created": f"{Fore.GREEN}✅ Authorization file oauth.json created!",
        "auth_err": f"{Fore.RED}❌ Error parsing 'headers.txt'. Make sure it's a valid cURL: ",
        "ytm_login_err": f"{Fore.RED}❌ Failed to login to YouTube Music: ",
        "menu_source": f"\n{Fore.CYAN}=== SELECT SOURCE ==={Style.RESET_ALL}\n1. Universal CSV (Recommended - Spotify/Apple/SC via Exportify/Soundiiz)\n2. YouTube Music (Direct API)\n3. Spotify (Direct API)\n4. Apple Music (Direct API)\n5. SoundCloud (Direct API)\n> ",
        "menu_target": f"\n{Fore.CYAN}=== SELECT TARGET ==={Style.RESET_ALL}\n1. YouTube Music (Direct API - Fully Working)\n2. Spotify (Direct API)\n3. Apple Music (Direct API)\n4. SoundCloud (Direct API)\n> ",
        "menu_mode": (
            f"\n{Fore.CYAN}=== SELECT MIGRATION MODE ==={Style.RESET_ALL}\n"
            "1. Full Library  — migrates every song in the CSV from start to finish\n"
            "2. Custom Range  — lets you specify a slice, e.g. tracks 100-500 only\n"
            "3. Dry Run       — searches for tracks WITHOUT liking them (safe test)\n> "
        ),
        "menu_range": "Enter range (e.g., 100-500): ",
        "menu_order": (
            f"\n{Fore.CYAN}=== PROCESSING ORDER ==={Style.RESET_ALL}\n"
            "This controls in what order songs end up in YouTube Music.\n"
            "YouTube Music puts the LAST liked song at the TOP of your library.\n"
            "  1. Top → Bottom  — row 1 of CSV is liked first → ends up at the BOTTOM\n"
            "  2. Bottom → Top  — last row liked first → row 1 ends up at the TOP\n"
            "💡 Tip: Choose option 2 if you want the newest songs at the top.\n> "
        ),
        "menu_smart": (
            f"\n{Fore.CYAN}=== SMART SEARCH ==={Style.RESET_ALL}\n"
            "Smart Search compares the duration of each search result against your CSV data.\n"
            "This prevents YouTube Music from accidentally picking a 10-hour loop version\n"
            "or a fan-remix instead of the real song (tolerance: ±90 seconds).\n"
            "  1. Yes — Enable Smart Search (recommended, requires duration in CSV)\n"
            "  2. No  — Pick the first result blindly (faster, less accurate)\n> "
        ),
        "menu_dest": (
            f"\n{Fore.CYAN}=== SELECT DESTINATION TYPE ==={Style.RESET_ALL}\n"
            "  1. Liked Songs (Default)\n"
            "  2. Specific Playlist\n> "
        ),
        "menu_playlist": (
            f"\n{Fore.CYAN}=== PLAYLIST OPTIONS ==={Style.RESET_ALL}\n"
            "  1. Create New Playlist\n"
            "  2. Use Existing Playlist\n> "
        ),
        "pl_title": "Enter new playlist title: ",
        "pl_desc": "Enter playlist description (optional): ",
        "pl_search": "Searching for your playlists...",
        "pl_select": "Enter the number of the playlist: ",
        "pl_created": f"{Fore.GREEN}✅ Playlist created: ",
        "invalid_range": f"{Fore.RED}❌ Invalid range.",
        "service_flaws": {
            "csv": f"{Fore.GREEN}✓ CSV Parsing: Reads any format. Universal and safe.",
            "ytm": f"{Fore.YELLOW}⚠️ YouTube Music: Uses header emulation. Prone to 401 Session Expiry. Rate limited.",
            "spotify": f"{Fore.YELLOW}⚠️ Spotify: API requires a registered Developer App (Client ID/Secret). Very strict rate limits.",
            "apple": f"{Fore.RED}❌ Apple Music: Completely closed ecosystem. Requires paid $99/yr Developer Token.",
            "soundcloud": f"{Fore.RED}❌ SoundCloud: Official API closed. Scraping breaks frequently."
        },
        "not_impl": f"{Fore.RED}❌ Direct API for this service is highly restricted. Please use 'Universal CSV' mode as SOURCE.",
        "starting": f"\n{Fore.CYAN}🚀 Starting migration...",
        "finished_already": f"{Fore.GREEN}✅ Migration completed!",
        "resuming": f"{Fore.YELLOW}♻️ Resuming from track #{{0}}...",
        "dry_run_warn": f"{Fore.YELLOW}⚠️ DRY RUN MODE: Tracks will only be searched.",
        "session_expired": f"\n{Fore.RED}⚠️ SESSION EXPIRED at track {{0}}! YouTube Music tokens need to be updated.",
        "session_ins": "Please update headers.txt with a new cURL, delete oauth.json, and restart.",
        "user_stop": f"\n{Fore.YELLOW}🛑 Stopped by user. Progress saved.",
        "final": f"\n{Fore.CYAN}📊 TOTAL: Processed: {{0}}/{{1}} | Migrated: {{2}} | Failed: {{3}}",
        "retry_msg": f"\n{Fore.YELLOW}Try again? (y/n): ",
        "exportify_ins": f"{Fore.CYAN}\n--- HOW TO GET CSV (Exportify) ---\n{Style.RESET_ALL}"
                        "1. Go to https://exportify.net/ and log in.\n"
                        "2. Find 'Liked Songs' and click 'Export'.\n"
                        "3. Rename the file to 'library.csv' and place it here.",
        "log_start": "--- NEW SESSION STARTED ---"
    },
    "ru": {
        "file_not_found": f"{Fore.RED}❌ Универсальный CSV файл не найден:",
        "put_csv": f"{Fore.YELLOW}Пожалуйста, положите файл библиотеки под названием 'library.csv' (подойдет экспорт откуда угодно) в папку со скриптом.",
        "headers_not_found": f"{Fore.RED}❌ Файл заголовков не найден:",
        "headers_ins": "1. Зайдите в YouTube Music и скопируйте любой запрос как 'cURL (bash)'.\n2. Создайте файл headers.txt и вставьте туда скопированный текст.",
        "setup_auth": f"{Fore.CYAN}🔧 Первичная настройка авторизации...",
        "auth_created": f"{Fore.GREEN}✅ Файл авторизации oauth.json успешно создан!",
        "auth_err": f"{Fore.RED}❌ Ошибка парсинга 'headers.txt': ",
        "ytm_login_err": f"{Fore.RED}❌ Не удалось авторизоваться в YouTube Music: ",
        "menu_source": f"\n{Fore.CYAN}=== ОТКУДА БЕРЕМ ТРЕКИ ==={Style.RESET_ALL}\n1. Универсальный CSV (Рекомендуется - подходит для Spotify/AppleMusic/SoundCloud)\n2. YouTube Music (Прямой API)\n3. Spotify (Прямой API)\n4. Apple Music (Прямой API)\n5. SoundCloud (Прямой API)\n> ",
        "menu_target": f"\n{Fore.CYAN}=== КУДА ПЕРЕНОСИМ ==={Style.RESET_ALL}\n1. YouTube Music (Прямой API - Работает на 100%)\n2. Spotify (Прямой API)\n3. Apple Music (Прямой API)\n4. SoundCloud (Прямой API)\n> ",
        "menu_mode": (
            f"\n{Fore.CYAN}=== РЕЖИМ МИГРАЦИИ ==={Style.RESET_ALL}\n"
            "1. Вся библиотека  — переносит все треки из CSV от начала до конца\n"
            "2. Диапазон        — указываете конкретные номера, например треки 100-500\n"
            "3. Тестовый режим  — ищет треки БЕЗ простановки лайков (безопасная проверка)\n> "
        ),
        "menu_range": "Введите диапазон (например, 100-500): ",
        "menu_order": (
            f"\n{Fore.CYAN}=== ПОРЯДОК ЗАГРУЗКИ ==={Style.RESET_ALL}\n"
            "Это управляет тем, в каком порядке песни окажутся в YouTube Music.\n"
            "YouTube Music всегда ставит ПОСЛЕДНИЙ залайканный трек в САМЫЙ ВЕРХ библиотеки.\n"
            "  1. Сверху-вниз  — первая строка CSV лайкается первой → окажется В САМОМ НИЗУ\n"
            "  2. Снизу-вверх  — последняя строка лайкается первой → первая строка окажется ВВЕРХУ\n"
            "💡 Совет: выбирайте вариант 2, если хотите, чтобы ваши самые старые треки были наверху.\n> "
        ),
        "menu_smart": (
            f"\n{Fore.CYAN}=== УМНЫЙ ПОИСК (Smart Search) ==={Style.RESET_ALL}\n"
            "Умный поиск сверяет длительность трека из CSV с результатами поиска.\n"
            "Это мешает алгоритму подобрать 10-часовую версию или фанатский ремикс\n"
            "вместо оригинала. Погрешность — до 90 секунд.\n"
            "  1. Да  — Включить умный поиск (рекомендуется, нужна длительность в CSV)\n"
            "  2. Нет — Брать первый попавшийся результат (быстрее, менее точно)\n> "
        ),
        "menu_dest": (
            f"\n{Fore.CYAN}=== КУДА ДОБАВЛЯЕМ ТРЕКИ? ==={Style.RESET_ALL}\n"
            "  1. В любимые (Лайки)\n"
            "  2. В конкретный плейлист\n> "
        ),
        "menu_playlist": (
            f"\n{Fore.CYAN}=== НАСТРОЙКИ ПЛЕЙЛИСТА ==={Style.RESET_ALL}\n"
            "  1. Создать новый плейлист\n"
            "  2. Выбрать из существующих\n> "
        ),
        "pl_title": "Введите название нового плейлиста: ",
        "pl_desc": "Введите описание (можно пустое): ",
        "pl_search": "Ищу ваши плейлисты...",
        "pl_select": "Введите номер плейлиста из списка: ",
        "pl_created": f"{Fore.GREEN}✅ Плейлист создан: ",
        "invalid_range": f"{Fore.RED}❌ Неверный диапазон.",
        "service_flaws": {
            "csv": f"{Fore.GREEN}✓ Универсальный CSV: Безопасно, читает скачанные базы файлов любого сервиса.",
            "ytm": f"{Fore.YELLOW}⚠️ YouTube Music: Обходной API. Часто блокирует сессию (ошибка 401), требуя обновления headers.",
            "spotify": f"{Fore.YELLOW}⚠️ Spotify: Для прямого API нужно регистрировать Developer App (Client ID/Secret) и долго настраивать токены.",
            "apple": f"{Fore.RED}❌ Apple Music: Закрытая экосистема. Для API нужен платный сертификат разработчика ($99/год).",
            "soundcloud": f"{Fore.RED}❌ SoundCloud: Официальный API давно закрыт. Парсеры постоянно ломаются интерфейсом."
        },
        "not_impl": f"{Fore.RED}❌ Прямое подключение к этому сервису слишком нестабильно из-за ограничений.\n👉 Пожалуйста, сделайте экспорт в CSV (через Soundiiz/TuneMyMusic/Exportify) и выберите Источник: Универсальный CSV.",
        "starting": f"\n{Fore.CYAN}🚀 Начинаем миграцию...",
        "finished_already": f"{Fore.GREEN}✅ Миграция уже завершена!",
        "resuming": f"{Fore.YELLOW}♻️ Возобновление с трека №{{0}}...",
        "dry_run_warn": f"{Fore.YELLOW}⚠️ ТЕСТОВЫЙ РЕЖИМ (Dry Run): Треки будут только найдены.",
        "session_expired": f"\n{Fore.RED}⚠️ СЕССИЯ ИСТЕКЛА на песне {{0}}! YouTube Music требует обновления токенов.",
        "session_ins": "Обновите headers.txt новым cURL запросом, удалите oauth.json и запустите заново.",
        "user_stop": f"\n{Fore.YELLOW}🛑 Остановка по команде пользователя. Прогресс сохранен.",
        "final": f"\n{Fore.CYAN}📊 ИТОГО: Обработано: {{0}}/{{1}} | Перенесено: {{2}} | Ошибок: {{3}}",
        "retry_msg": f"\n{Fore.YELLOW}Попробовать снова? (y/n): ",
        "exportify_ins": f"{Fore.CYAN}\n--- КАК ПОЛУЧИТЬ CSV (Exportify) ---\n{Style.RESET_ALL}"
                        "1. Зайдите на https://exportify.net/ и авторизуйтесь.\n"
                        "2. Найдите 'Liked Songs' и нажмите кнопку 'Export'.\n"
                        "3. Переименуйте файл в 'library.csv' и положите в папку со скриптом.",
        "log_start": "--- НОВАЯ СЕССИЯ ЗАПУЩЕНА ---"
    }
}

def get_language():
    print(LOGO)
    print("Choose your language / Выберите язык:")
    print("1. English")
    print("2. Русский")
    choice = input("> ").strip()
    return 'ru' if choice == '2' else 'en'

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

def load_headers(filepath):
    # Try different encodings for weird windows notepad saves
    for enc in ['utf-8', 'utf-16', 'utf-8-sig', 'cp1251']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read().strip()
                if content: return content
        except Exception:
            pass
    # Fallback to binary with ignore if all fails
    try:
        with open(filepath, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore').strip()
    except Exception:
        return ""

def log_failed_song(idx, query, reason):
    file_exists = os.path.isfile(FAILED_CSV_PATH)
    with open(FAILED_CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Track Index', 'Query', 'Reason'])
        writer.writerow([idx, query, reason])

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
    with open(filepath, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        # Detective work for columns
        track_col = next((k for k in reader.fieldnames if k.lower() in ['track name', 'title', 'song', 'name', 'track']), None)
        artist_col = next((k for k in reader.fieldnames if k.lower() in ['artist name(s)', 'artist', 'creator', 'artist name', 'artists']), None)
        dur_col = next((k for k in reader.fieldnames if k.lower() in ['track duration (ms)', 'duration', 'length', 'time (ms)', 'time']), None)

        if not track_col and not artist_col:
            track_col = reader.fieldnames[0] if len(reader.fieldnames) > 0 else None
            artist_col = reader.fieldnames[1] if len(reader.fieldnames) > 1 else None

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
    log_to_file(f"Successfully parsed {len(songs)} songs from CSV.")
    return songs

def main():
    lang_code = get_language()
    t = LANG_DATA[lang_code]
    log_to_file(f"Session started. Language: {lang_code}")

    # Source Selection
    source_input = input(t['menu_source']).strip()
    log_to_file(f"Source selected: {source_input}")
    if source_input == "2":
        print(t['service_flaws']['ytm'])
        print(t['not_impl'])
        return
    elif source_input == "3":
        print(t['service_flaws']['spotify'])
        print(t['not_impl'])
        return
    elif source_input == "4":
        print(t['service_flaws']['apple'])
        print(t['not_impl'])
        return
    elif source_input == "5":
        print(t['service_flaws']['soundcloud'])
        print(t['not_impl'])
        return
    elif source_input != "1":
        return
    
    # If 1 (Universal CSV)
    print(t['service_flaws']['csv'])
    print(t['exportify_ins'])

    # Target Selection
    while True:
        target_input = input(t['menu_target']).strip()
        log_to_file(f"Target selected: {target_input}")
        if target_input == "1":
            break
        elif target_input in ["2", "3", "4"]:
            print(t['not_impl'])
        else:
            print(f"{Fore.RED}❌ Invalid choice.")
        
        if input(t['retry_msg']).lower() != 'y':
            return

    # If Target is YT Music
    print(t['service_flaws']['ytm'])

    # Setup Loop for CSV and Auth
    while True:
        actual_csv = CSV_PATH if os.path.exists(CSV_PATH) else os.path.join(BASE_DIR, "liked.csv")
        
        # Check CSV
        if not os.path.exists(actual_csv):
            print(f"{t['file_not_found']} {CSV_PATH}")
            print(t['put_csv'])
            if input(t['retry_msg']).lower() == 'y': continue
            else: return

        # Auth Setup
        if not os.path.exists(AUTH_JSON_PATH):
            if not os.path.exists(HEADERS_PATH):
                # Feature: paste cURL directly into the terminal
                print(f"\n{Fore.YELLOW}📋 Файл headers.txt не найден.")
                print(f"{Fore.CYAN}Вы можете вставить cURL прямо сейчас, не создавая файл вручную!")
                print(f"{Fore.WHITE}Как получить cURL:")
                print("  1. Откройте music.youtube.com в браузере (убедитесь, что вошли в аккаунт).")
                print("  2. Нажмите F12 → Network (Сеть).")
                print("  3. В поле поиска введите 'browse', обновите страницу.")
                print("  4. Правой кнопкой по запросу 'browse' → Copy → Copy as cURL (bash).")
                print(f"{Fore.YELLOW}Вставьте cURL ниже и нажмите Enter (или оставьте пустым для отмены):{Style.RESET_ALL}")
                
                lines = []
                try:
                    while True:
                        line = input()
                        if not line and lines:
                            break
                        if line:
                            lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    pass
                
                if lines:
                    pasted_curl = "\n".join(lines)
                    with open(HEADERS_PATH, 'w', encoding='utf-8') as hf:
                        hf.write(pasted_curl)
                    print(f"{Fore.GREEN}✅ headers.txt создан автоматически!")
                else:
                    print(f"{Fore.RED}❌ Ничего не вставлено.")
                    if input(t['retry_msg']).lower() == 'y': continue
                    else: return
            
            print(t['setup_auth'])
            try:
                raw_content = load_headers(HEADERS_PATH).strip()
                low_content = raw_content.lower()
                
                if low_content.startswith("http"):
                    print(f"\n{Fore.RED}❌ ОШИБКА: Вы вставили обычную ссылку (URL) вместо команды cURL!")
                    print(f"{Fore.YELLOW}Нужно нажать правой кнопкой мыши по запросу -> 'Copy' -> 'Copy as cURL (bash)'.")
                    if input(t['retry_msg']).lower() == 'y': continue
                    else: return

                # Check for critical absence of cookie early
                # setup_browser() expects raw "header: value" lines, NOT a curl command
                # So we must parse the cURL ourselves
                if low_content.startswith("curl"):
                    raw_headers_lines = []
                    
                    # Extract all -H 'header: value' entries
                    header_matches = re.findall(r"-H '([^']+)'", raw_content)
                    header_matches += re.findall(r'-H "([^"]+)"', raw_content)
                    for h in header_matches:
                        raw_headers_lines.append(h)
                    
                    # Extract -b 'cookie_string' (Chrome puts cookies here instead of -H)
                    cookie_matches = re.findall(r"-b '([^']+)'", raw_content)
                    cookie_matches += re.findall(r'-b "([^"]+)"', raw_content)
                    for c in cookie_matches:
                        raw_headers_lines.append(f"cookie: {c}")
                    
                    if not raw_headers_lines:
                        print(f"\n{Fore.RED}❌ ОШИБКА: Не удалось найти заголовки в cURL команде!")
                        if input(t['retry_msg']).lower() == 'y': continue
                        else: return
                    
                    raw_content = "\n".join(raw_headers_lines)
                    low_content = raw_content.lower()

                # Check for critical absence of cookie early

                if "cookie" not in low_content:
                    print(f"\n{Fore.RED}❌ ОШИБКА: Заголовок 'cookie' не найден в {HEADERS_PATH}!")
                    safe_print = raw_content[:80].replace('\n', ' ')
                    print(f"{Fore.YELLOW}Отладка: Скрипт видит такой текст: '{safe_print}...'\nДлина текста: {len(raw_content)} символов.")
                    print(f"👉 Убедитесь, что вы скопировали ВЕСЬ блок cURL (bash) из запроса 'browse' целиком.")
                    if input(t['retry_msg']).lower() == 'y': continue
                    else: return

                # Auto-inject x-goog-authuser if missing and if it's a bash cURL
                if "x-goog-authuser" not in low_content:
                    if low_content.startswith("curl"):
                        # Remove trailing chars to cleanly append
                        raw_content = raw_content.rstrip().rstrip('\\').rstrip(';')
                        raw_content += " -H 'x-goog-authuser: 0'"
                    else:
                        raw_content += "\nx-goog-authuser: 0"

                
                # Try to setup
                setup_browser(AUTH_JSON_PATH, raw_content)
                print(t['auth_created'])
                log_to_file("Auth file created successfully.")
            except Exception as e:
                error_str = str(e)
                log_to_file(f"Auth creation failed: {error_str}")
                print(f"{t['auth_err']}\n{error_str}")
                print(f"{Fore.YELLOW}Hint: Make sure headers.txt contains EXACTLY ONE 'cURL (bash)' request.")
                if "^" in raw_content:
                    print(f"{Fore.RED}⚠️ Windows Users: Do NOT choose 'cURL (cmd)'. You must select 'cURL (bash)'.")
                if input(t['retry_msg']).lower() == 'y': continue
                else: return

        try:
            ytm = YTMusic(AUTH_JSON_PATH)
            break # Success, exit setup loop
        except Exception as e:
            print(f"{t['ytm_login_err']}{e}")
            log_to_file(f"YTM login error: {str(e)}")
            if os.path.exists(AUTH_JSON_PATH): os.remove(AUTH_JSON_PATH)
            if input(t['retry_msg']).lower() == 'y': continue
            else: return
        
    # Read Universal CSV
    songs = universal_csv_parser(actual_csv)
    total_csv = len(songs)

    if total_csv == 0:
        print(f"{Fore.RED}❌ CSV file is empty or formatted incorrectly.")
        return

    # Menu Options
    mode = input(t['menu_mode']).strip()
    log_to_file(f"Migration mode selected: {mode}")
    is_dry_run = (mode == "3")
    custom_range = False
    start_idx = 0
    end_idx = total_csv

    if mode == "2":
        r_input = input(t['menu_range']).strip()
        log_to_file(f"Range input: {r_input}")
        match = re.match(r'^(\d+)-(\d+)$', r_input)
        if match:
            start_idx = max(0, int(match.group(1)) - 1)
            end_idx = min(total_csv, int(match.group(2)))
            custom_range = True
        else:
            print(t['invalid_range'])
            return

    order_input = input(t['menu_order']).strip()
    log_to_file(f"Order input: {order_input}")
    if order_input == "2":
        songs.reverse()
        
    smart_input = input(t['menu_smart']).strip()
    log_to_file(f"Smart Search input: {smart_input}")
    is_smart = (smart_input == "1")

    # Playlist Selection
    target_playlist_id = None
    if not is_dry_run:
        dest_choice = input(t['menu_dest']).strip()
        if dest_choice == "2":
            pl_choice = input(t['menu_playlist']).strip()
            if pl_choice == "1":
                title = input(t['pl_title']).strip() or "Migratify Playlist"
                desc = input(t['pl_desc']).strip() or "Migrated via Migratify"
                target_playlist_id = ytm.create_playlist(title, desc)
                print(f"{t['pl_created']} {title}")
            else:
                print(t['pl_search'])
                playlists = ytm.get_library_playlists(limit=50)
                for i, pl in enumerate(playlists):
                    print(f"{i+1}. {pl['title']} ({pl['itemCount']} tracks)")
                p_idx = int(input(t['pl_select']).strip()) - 1
                target_playlist_id = playlists[p_idx]['playlistId']

    # Progress load
    progress = load_progress()
    total = end_idx - start_idx

    if not custom_range and not is_dry_run:
        start_idx = progress["processed_rows"]
    elif custom_range:
        progress = {"migrated_count": 0, "processed_rows": start_idx, "failed_rows": 0}

    if start_idx >= end_idx:
        print(t['finished_already'])
        return

    if is_dry_run:
        print(f"\\n{t['dry_run_warn']}")

    print(t['starting'])
    
    if start_idx > 0 and not is_dry_run and not custom_range:
        print(t['resuming'].format(start_idx + 1))

    songs_to_process = songs[start_idx:end_idx]
    current_index = start_idx

    try:
        pbar = tqdm(songs_to_process, desc="Migrating", unit="song")
        for offset, song_data in enumerate(pbar):
            current_index = start_idx + offset
            
            artist_name = song_data["artist"]
            track_name = song_data["track"]
            target_sec = song_data["target_sec"]
            
            query = f"{artist_name} - {track_name}".strip(" -")
            if not query:
                continue
            
            try:
                search_results = ytm.search(query, filter="songs")
                matched_video_id = None
                
                if search_results:
                    if is_smart and target_sec:
                        for item in search_results:
                            item_dur = get_duration_sec(item.get('duration'))
                            if item_dur and abs(item_dur - target_sec) <= 90:
                                matched_video_id = item['videoId']
                                break
                        if not matched_video_id:
                            matched_video_id = search_results[0]['videoId'] # Fallback
                    else:
                        matched_video_id = search_results[0]['videoId']
                        
                if matched_video_id:
                    if not is_dry_run:
                        if target_playlist_id:
                            ytm.add_playlist_items(target_playlist_id, [matched_video_id])
                        else:
                            ytm.rate_song(matched_video_id, 'LIKE')
                    
                    progress["migrated_count"] += 1
                    status_text = f"{Fore.GREEN}OK" if not is_dry_run else f"{Fore.GREEN}Found"
                    # log_to_file(f"SUCCESS: [{current_index + 1}] {query} -> Found Video ID: {matched_video_id}")
                else:
                    progress["failed_rows"] += 1
                    status_text = f"{Fore.RED}FAIL"
                    # log_to_file(f"FAILURE: [{current_index + 1}] {query} -> Not found on YT Music.")
                    log_failed_song(current_index + 1, query, "Not found in search")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    pbar.close()
                    print(t['session_expired'].format(current_index + 1))
                    print(t['session_ins'])
                    break
                
                progress["failed_rows"] += 1
                status_text = f"{Fore.YELLOW}ERR"
                log_failed_song(current_index + 1, query, error_msg)

            progress["processed_rows"] = current_index + 1
            
            # Simple clean output for tqdm
            pbar.set_postfix_str(f"{status_text} | {track_name[:20]}")
            
            if offset % 10 == 0 or offset == len(songs_to_process) - 1:
                if not is_dry_run and not custom_range:
                    save_progress(progress)
                
                if not is_dry_run:
                    time.sleep(0.3)
    except KeyboardInterrupt:
        print(t['user_stop'])
    finally:
        if not is_dry_run and not custom_range:
            save_progress(progress)
        print(t['final'].format(progress['processed_rows'] - start_idx, total, progress['migrated_count'], progress['failed_rows']))
        log_to_file(f"Migration completed. Processed: {progress['processed_rows'] - start_idx}, Total: {total}, Migrated: {progress['migrated_count']}, Failed: {progress['failed_rows']}")

if __name__ == '__main__':
    main()

import csv
import os
import time
import json
import re
from ytmusicapi import YTMusic
from ytmusicapi.setup import setup_browser
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "library.csv") # Renamed generically
HEADERS_PATH = os.path.join(BASE_DIR, "headers.txt")
AUTH_JSON_PATH = os.path.join(BASE_DIR, "oauth.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "progress.json")
FAILED_CSV_PATH = os.path.join(BASE_DIR, "failed_songs.csv")
LOGS_PATH = os.path.join(BASE_DIR, "logs.txt")

def log_to_file(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGS_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

LOGO = fr"""{Fore.MAGENTA}{Style.BRIGHT}
  __  __ _                 _   _  __       
 |  \/  (_)               | | (_)/ _|      
 | \  / |_  __ _ _ __ __ _| |_ _| |_ _   _ 
 | |\/| | |/ _` | '__/ _` | __| |  _| | | |
 | |  | | | (_| | | | (_| | |_| | | | |_| |
 |_|  |_|_|\__, |_|  \__,_|\__|_|_|  \__, |
            __/ |                     __/ |
           |___/                     |___/ 
{Fore.CYAN}       By Noxbane      {Style.RESET_ALL}
"""

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
        "menu_mode": "\nSelect migration mode:\n1. Migrate full library\n2. Migrate a specific range of tracks\n3. Dry Run (Search without liking)\n> ",
        "menu_range": "Enter range (e.g., 100-500): ",
        "menu_order": "\nSelect processing order:\n1. Default (Top to Bottom)\n2. Reversed (Bottom to Top)\n> ",
        "menu_smart": "\n* **Smart Search**: Filters search results on YouTube by exact duration matching (within 90 seconds) so it doesn't accidentally pick a \"10-hour loop version\" or a fan-remix.\n1. Yes\n2. No\n> ",
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
        "menu_mode": "\nВыберите режим миграции:\n1. Перенести всю библиотеку полностью\n2. Перенести указанный диапазон треков (например, 100-500)\n3. Тестовый режим (Dry Run) — только поиск\n> ",
        "menu_range": "Введите диапазон (например, 100-500): ",
        "menu_order": "\nВыберите порядок загрузки:\n1. Стандартный (Сверху-вниз)\n2. Реверс (Снизу-вверх)\n> ",
        "menu_smart": "\n* **Умный поиск (Smart Search)**: Скрипт сверяет длительность трека, чтобы алгоритм случайно не добавил 10-часовую версию или фанатский ремикс вместо оригинальной песни (погрешность до 90 секунд).\n1. Да\n2. Нет\n> ",
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
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

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
                print(f"{t['headers_not_found']} {HEADERS_PATH}")
                print(t['headers_ins'])
                if input(t['retry_msg']).lower() == 'y': continue
                else: return
            
            print(t['setup_auth'])
            try:
                raw_content = load_headers(HEADERS_PATH).strip()
                low_content = raw_content.lower()
                
                # Check for critical absence of cookie early
                if "cookie" not in low_content:
                    print(f"\n{Fore.RED}❌ ERROR: 'cookie' not found in headers!")
                    print(f"{Fore.YELLOW}Tip: You probably copied an image/font request. Search for 'browse' or 'next' in the Network tab and copy THAT request as cURL (bash).")
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
        for offset, song_data in enumerate(songs_to_process):
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
                        ytm.rate_song(matched_video_id, 'LIKE')
                    
                    progress["migrated_count"] += 1
                    status_text = f"{Fore.GREEN}✅ {'Smart OK' if is_smart else 'OK'}" if not is_dry_run else f"{Fore.GREEN}✅ Found"
                    log_to_file(f"SUCCESS: [{current_index + 1}] {query} -> Found Video ID: {matched_video_id}")
                else:
                    progress["failed_rows"] += 1
                    status_text = f"{Fore.RED}❌ Not found"
                    log_to_file(f"FAILURE: [{current_index + 1}] {query} -> Not found on YT Music.")
                    log_failed_song(current_index + 1, query, "Not found in search")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print(t['session_expired'].format(current_index + 1))
                    print(t['session_ins'])
                    log_to_file(f"CRITICAL ERROR: Session expired at index {current_index + 1}. Error: {error_msg}")
                    break
                
                progress["failed_rows"] += 1
                status_text = f"{Fore.YELLOW}⚠️ Error: {str(e)[:20]}"
                log_to_file(f"ERROR: [{current_index + 1}] {query} -> Exception: {error_msg}")
                log_failed_song(current_index + 1, query, error_msg)

            progress["processed_rows"] = current_index + 1

            if offset % 10 == 0 or offset == len(songs_to_process) - 1:
                print(f"[{current_index + 1}/{end_idx}] | {status_text}{Style.RESET_ALL} | {query[:45]}")
                if not is_dry_run and not custom_range:
                    save_progress(progress)
                
                if not is_dry_run:
                    time.sleep(0.5)
                
    except KeyboardInterrupt:
        print(t['user_stop'])
    finally:
        if not is_dry_run and not custom_range:
            save_progress(progress)
        print(t['final'].format(progress['processed_rows'] - start_idx, total, progress['migrated_count'], progress['failed_rows']))
        log_to_file(f"Migration completed. Processed: {progress['processed_rows'] - start_idx}, Total: {total}, Migrated: {progress['migrated_count']}, Failed: {progress['failed_rows']}")

if __name__ == '__main__':
    main()

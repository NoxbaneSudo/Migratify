# Migratify

Migratify is a small Python tool for moving a music library from a CSV export into YouTube Music. It reads a `library.csv` file, searches for matching tracks, likes them in YouTube Music, and keeps enough state to resume if the session expires.

[English version](#english-version)

## Возможности

- Импорт треков из CSV-экспорта Spotify, Apple Music, SoundCloud и других сервисов.
- Поиск совпадений в YouTube Music с учетом длительности трека.
- Продолжение с места остановки через `progress.json`.
- Список неудачных переносов в `failed_songs.csv`.
- Автоматическая установка Python-зависимостей при первом запуске.

## Что поддерживается

YouTube Music поддерживается как сервис назначения без регистрации приложения разработчика.

Перенос напрямую в Spotify, Apple Music или SoundCloud как в сервис назначения не реализован: для этого нужны отдельные Developer App, API-ключи и ограничения конкретных платформ. Сейчас эти сервисы рассматриваются только как источники CSV-экспорта.

## Установка

Требуется [Python 3.8+](https://www.python.org/downloads/).

1. Скачайте или клонируйте репозиторий.
2. Откройте терминал в папке проекта.
3. Запустите скрипт. При первом запуске он установит нужные зависимости.

## 1. Подготовьте `library.csv`

Скрипт ожидает файл `library.csv` в папке проекта. Ниже — практичные способы получить такой файл из популярных сервисов.

### Spotify

1. Откройте [Exportify](https://exportify.net/).
2. Войдите в аккаунт Spotify.
3. Экспортируйте `Liked Songs` или нужный плейлист.
4. Переименуйте скачанный файл в `library.csv` и положите его в папку Migratify.

### Apple Music

1. Откройте [TuneMyMusic](https://www.tunemymusic.com/ru/) или [Soundiiz](https://soundiiz.com/).
2. Выберите Apple Music как источник.
3. Выберите экспорт в файл CSV или Excel.
4. Переименуйте результат в `library.csv` и положите его в папку Migratify.

### SoundCloud

1. Откройте [TuneMyMusic](https://www.tunemymusic.com/ru/) или [Soundiiz](https://soundiiz.com/).
2. Выберите SoundCloud как источник.
3. Экспортируйте библиотеку или плейлист в CSV.
4. Переименуйте файл в `library.csv` и положите его в папку Migratify.

## 2. Настройте доступ к YouTube Music

Migratify использует данные текущей браузерной сессии YouTube Music.

1. Откройте [music.youtube.com](https://music.youtube.com/) и войдите в аккаунт.
2. Откройте инструменты разработчика: `F12`, `Ctrl+Shift+I` или `Cmd+Opt+I` на macOS.
3. Перейдите на вкладку Network / Сеть.
4. В фильтре введите `browse` и обновите страницу.
5. Нажмите правой кнопкой на любой запрос `browse` и выберите `Copy` → `Copy as cURL (bash)`.
6. При запуске вставьте cURL в скрипт или сохраните его в файл `headers.txt` в папке проекта.

На Windows выбирайте именно `Copy as cURL (bash)`, а не вариант для `cmd`.

## 3. Запустите миграцию

### Быстрый запуск

| Платформа | Файл | Как запускать |
| --- | --- | --- |
| Windows | `start.bat` | Двойной клик |
| Linux / macOS | `start.sh` | Запуск в терминале |

Если `start.sh` не запускается, выдайте права на выполнение:

```bash
chmod +x start.sh
```

### Запуск через терминал

```bash
python migrate.py
```

На некоторых системах команда может называться `python3`:

```bash
python3 migrate.py
```

Дальше следуйте подсказкам в терминале.

## Если сессия истекла

YouTube Music может сбросить сессию при большом количестве действий. Если появилась ошибка `Session Expired` или `401 Unauthorized`:

1. Не удаляйте `progress.json` — в нем сохранен прогресс.
2. Откройте YouTube Music в браузере и обновите страницу.
3. Снова скопируйте свежий `Copy as cURL (bash)` по инструкции выше.
4. Замените содержимое `headers.txt` новым cURL.
5. Удалите `oauth.json`, если он есть.
6. Запустите скрипт снова и выберите продолжение миграции.

## Благодарности

- [ytmusicapi](https://github.com/sigma67/ytmusicapi) — библиотека для работы с YouTube Music.
- Marseille и c1mcp2 — помогли найти и исправить проблему с парсингом cURL-заголовков.

---

# English Version

Migratify is a small Python tool for moving a music library from a CSV export into YouTube Music. It reads a `library.csv` file, searches for matching tracks, likes them in YouTube Music, and keeps enough state to resume if the session expires.

## Features

- Import tracks from CSV exports created from Spotify, Apple Music, SoundCloud, and other services.
- Match YouTube Music results using track duration.
- Resume from the last processed track with `progress.json`.
- Save tracks that could not be migrated to `failed_songs.csv`.
- Install Python dependencies automatically on first launch.

## Supported target

YouTube Music is supported as the destination without creating a developer app.

Spotify, Apple Music, and SoundCloud are not supported as direct destinations in this project. They require separate developer apps, API keys, and platform-specific approval flows. In Migratify, they are treated as CSV sources.

## Installation

You need [Python 3.8+](https://www.python.org/downloads/).

1. Download or clone this repository.
2. Open a terminal in the project folder.
3. Run the script. It will install required dependencies on first launch.

## 1. Prepare `library.csv`

The script expects a `library.csv` file in the project folder.

### Spotify

1. Open [Exportify](https://exportify.net/).
2. Log in with your Spotify account.
3. Export `Liked Songs` or another playlist.
4. Rename the downloaded file to `library.csv` and place it in the Migratify folder.

### Apple Music

1. Open [TuneMyMusic](https://www.tunemymusic.com/) or [Soundiiz](https://soundiiz.com/).
2. Select Apple Music as the source.
3. Export to a CSV or Excel file.
4. Rename the result to `library.csv` and place it in the Migratify folder.

### SoundCloud

1. Open [TuneMyMusic](https://www.tunemymusic.com/) or [Soundiiz](https://soundiiz.com/).
2. Select SoundCloud as the source.
3. Export the library or playlist to CSV.
4. Rename the file to `library.csv` and place it in the Migratify folder.

## 2. Set up YouTube Music access

Migratify uses your current YouTube Music browser session.

1. Open [music.youtube.com](https://music.youtube.com/) and make sure you are logged in.
2. Open Developer Tools with `F12`, `Ctrl+Shift+I`, or `Cmd+Opt+I` on macOS.
3. Go to the Network tab.
4. Type `browse` in the filter and refresh the page.
5. Right-click any `browse` request and choose `Copy` → `Copy as cURL (bash)`.
6. Paste the cURL into the script when prompted, or save it in `headers.txt` in the project folder.

On Windows, choose `Copy as cURL (bash)`, not the `cmd` variant.

## 3. Run migration

### Quick launch

| Platform | File | How to run |
| --- | --- | --- |
| Windows | `start.bat` | Double-click |
| Linux / macOS | `start.sh` | Run in terminal |

If `start.sh` does not run, grant execute permissions:

```bash
chmod +x start.sh
```

### Terminal launch

```bash
python migrate.py
```

On some systems, use `python3` instead:

```bash
python3 migrate.py
```

Then follow the terminal prompts.

## If the session expires

YouTube Music can expire the session after many automated actions. If you see `Session Expired` or `401 Unauthorized`:

1. Do not delete `progress.json`; it stores the migration progress.
2. Open YouTube Music in the browser and refresh the page.
3. Copy a fresh `Copy as cURL (bash)` request using the steps above.
4. Replace the contents of `headers.txt` with the new cURL.
5. Delete `oauth.json` if it exists.
6. Run the script again and choose to resume.

## Acknowledgements

- [ytmusicapi](https://github.com/sigma67/ytmusicapi) — the library used for YouTube Music access.
- Marseille and c1mcp2 — helped identify and fix the cURL header parsing issue.

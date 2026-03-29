# Migratify 🇷🇺 / 🇬🇧

*[🇬🇧 English translated below](#-english-version)*

Универсальный, кроссплатформенный комбайн для миграции вашей музыкальной библиотеки из любого стримингового сервиса (Spotify, Apple Music, SoundCloud) в YouTube Music.

Инструмент обходит ограничения закрытых API и платных лицензий разработчиков, используя универсальный парсер `.csv` файлов и эмуляцию веб-запросов. Вы можете бесплатно перенести тысячи своих песен без дубликатов, банов и потери прогресса!

## 🚀 Особенности
* **Универсальный парсер CSV**: Вы можете "скормить" скрипту файл экспорта из любого сервиса. Он сам поймет, в какой колонке находится название трека, а в какой — автор или длительность.
* **Умный поиск (Smart Search)**: Скрипт сверяет длительность трека, чтобы алгоритм случайно не добавил 10-часовую версию или фанатский ремикс вместо оригинальной песни (погрешность до 90 секунд).
* **Модульная архитектура**: Выбор источников и целей прямо из меню терминала. На данный момент 100% поддерживается связка `Универсальный CSV ➔ YouTube Music`.
* **Умное авто-возобновление**: Если ваш токен истечет из-за сброса сессии (ошибка 401: Unauthorized), весь прогресс сохранится. Просто обновите куки, и он продолжит с той же песни без двойных лайков.
* **Продвинутые режимы**: Перенесите всю библиотеку, укажите точный диапазон (например, треки `100-500`) или запустите **Тестовый режим (Dry Run)**, чтобы скрипт просто поискал треки без проставления лайков.
* **Реверс-режим**: Запустите скрипт снизу-вверх, чтобы самые старые треки в YouTube Music оказались в самом низу вашего плейлиста.
* **Система логов**: Автоматически создает `logs.txt` для технической отладки и `failed_songs.csv` со списком тех песен, которые не нашлись.

## 📥 Установка (Windows / Linux / Mac)

**Требования:** На вашем компьютере должен быть установлен [Python 3.8+](https://www.python.org/downloads/).

1. Скачайте этот репозиторий к себе на ПК.
2. Откройте терминал/командную строку в папке скрипта.
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Шаг 1: Получение треков (Источник)

Чтобы перенести музыку, нам нужен файл логов библиотеки. Выберите ваш текущий сервис, разверните инструкцию и скачайте базу в формате файла `library.csv`:

<details>
<summary><b style="font-size: 1.1em; color: #1DB954;">🎵 Spotify</b></summary>
<br>
Прямой API Spotify требует наличия Premium-подписки у разработчиков. Поэтому самый надежный способ — GDPR-экспорт плейлиста:

1. Перейдите на бесплатный сайт [Exportify](https://exportify.net/).
2. Дайте доступ к своему аккаунту Spotify (это безопасно).
3. Найдите в списке **"Liked Songs"** (или любой другой плейлист).
4. Нажмите **Export** (выгрузка).
5. Переименуйте скачанный файл ровно в <code>library.csv</code> и положите в папку со скриптом <b>Migratify</b>.
</details>

<details>
<summary><b style="font-size: 1.1em; color: #fa243c;">🎵 Apple Music</b></summary>
<br>
Apple Music — это очень закрытая экосистема, которая не позволяет получать данные через API без купленной лицензии разработчика ($99/год).

1. Перейдите на бесплатный сервис [TuneMyMusic](https://www.tunemymusic.com/ru/) или [Soundiiz](https://soundiiz.com/).
2. Пройдите авторизацию через Apple Music как **"Источник"**.
3. В качестве **"Цели"** выберите экспорт в файл — формат **CSV / Excel**.
4. После скачивания переименуйте файл ровно в <code>library.csv</code> и положите в папку со скриптом <b>Migratify</b>.
</details>

<details>
<summary><b style="font-size: 1.1em; color: #ff5500;">🎵 SoundCloud</b></summary>
<br>
SoundCloud давно закрыл регистрацию новых приложений для разработчиков, поэтому сторонние скрипты могут часто ломаться. Использование CSV файла — гарант надежности.

1. Перейдите на бесплатный сервис [TuneMyMusic](https://www.tunemymusic.com/ru/) или [Soundiiz](https://soundiiz.com/).
2. Привяжите ваш аккаунт SoundCloud как **"Источник"**.
3. В качестве **"Цели"** выберите экспорт в файл — формат **CSV**.
4. После скачивания переименуйте файл ровно в <code>library.csv</code> и положите в папку со скриптом <b>Migratify</b>.
</details>

---

## 🔑 Шаг 2: Настройка назначения (Цель)

Скрипту нужен доступ к вашему аккаунту назначения, чтобы лайкать треки. Выберите сервис, куда будут перенесены ваши песни:

<details>
<summary><b style="font-size: 1.1em; color: #FF0000;">🎧 YouTube Music</b></summary>
<br>
Так как у YT Music нет прозрачного API для пользователей, скрипту нужны данные вашей текущей сессии из веб-браузера:

1. Откройте [music.youtube.com](https://music.youtube.com/) в браузере и убедитесь, что вы авторизованы.
2. Откройте **"Инструменты Разработчика"** (кнопка `F12` или `Ctrl+Shift+I` в Windows/Linux, `Cmd+Opt+I` в Mac).
3. Перейдите на вкладку **Network (Сеть)**.
4. Обновите страницу (`F5`) или попробуйте что-то найти в поиске на сайте. У вас появится куча запросов.
5. Найдите запрос с названием `browse` или `next` (это внутренние запросы ютуба).
6. Нажмите по этому запросу **ПРАВОЙ Кнопкой Мыши** ➔ **Copy (Копировать)** ➔ **Copy as cURL (bash)**. <br>*(Важно: На Windows всегда выбирайте именно cURL (bash), а не cURL (cmd)!)*
7. Создайте пустой текстовый файл `headers.txt` в папке со скриптом, вставьте туда этот огромный скопированный текст и сохраните. Готово!
</details>

---

## 🏎️ Шаг 3: Запуск миграции

Запустите скрипт командой:
```bash
python migrate.py
```
*(На Mac/Ubuntu, команда может быть `python3 migrate.py`)*

Следуйте меню на экране (язык, источник треков, включение/выключение умного поиска).

### ⚠️ Решение проблемы "Session Expired / 401 Unauthorized"
YouTube Music часто сбрасывает "нетипичную" активность (например 1000+ проставленных лайков за час). Если скрипт остановится:
1. Без паники! Весь прогресс сохранен в файле `progress.json`. Мы не начнем всё сначала.
2. Зайдите в браузер в YouTube Music, обновите страницу и **повторите Шаг 2**, скопировав свежий `cURL` запрос.
3. Полностью замените текст в файле `headers.txt` на только что скопированный текст.
4. **Удалите файл `oauth.json`** из папки (чтобы скрипт не пытался использовать старый файл).
5. Снова запустите скрипт. Он предложит возобновить миграцию ровно с того трека, где остановился!

## 🤝 Благодарности (Acknowledgements)
* **[ytmusicapi](https://github.com/sigma67/ytmusicapi)** by `sigma67` — библиотека для YouTube Music на Python.

---

# 🇬🇧 English Version

A universal cross-platform Swiss Army knife to migrate your music library from any streaming service to YouTube Music.

This tool bypasses closed APIs and paid developer license restrictions by relying on a universal `.csv` parser and web request emulation. You can transfer thousands of liked songs completely for free without duplicating tracks or getting rate-banned!

## 🚀 Features
* **Universal CSV Parser**: Feed the script a `.csv` export from anywhere. It intelligently detects track names, artists, and duration columns natively, making Apple Music or SoundCloud uploads a breeze.
* **Smart Search**: Filters search results on YouTube by exact duration matching (within 90 seconds) so it doesn't accidentally pick a "10-hour loop version" or a fan-remix.
* **Modular Architecture**: Terminal menu lets you select Source and Target ecosystems with detailed instructions. Current fully tested path: `Universal CSV ➔ YouTube Music`.
* **Smart Auto-Resume**: The script remembers exactly where it stopped. If your tokens expire (401 error), you can fetch new ones, and it will resume right where it left off!

* **Failed Tracks Export**: Automatically creates a `failed_songs.csv` log for tracks it couldn't reliably find, so you can manually review/add them later.

## 📥 Installation

Ensure you have [Python 3.8+](https://www.python.org/downloads/) installed.

1. Download or clone this repository.
2. Open terminal in the scripts folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Step 1: Exporting Tracks (Source)

You'll need an export file containing your tracks. Click on your platform below to reveal the easiest way to generate a `library.csv` file:

<details>
<summary><b style="font-size: 1.1em; color: #1DB954;">🎵 Spotify</b></summary>
<br>
Using Spotify's API directly requires Premium. Utilizing static `.csv` exports is much more reliable:

1. Go to the free tool [Exportify](https://exportify.net/).
2. Log in with your Spotify account.
3. Find your **"Liked Songs"** (or another playlist) and hit **Export**.
4. Rename the downloaded file to exactly <code>library.csv</code> and place it inside the Migratify script folder.
</details>

<details>
<summary><b style="font-size: 1.1em; color: #fa243c;">🎵 Apple Music</b></summary>
<br>
Apple Music is notoriously locked down without a paid $99/yr Apple Developer account. Use a bridge service instead:

1. Visit [TuneMyMusic](https://www.tunemymusic.com/) or [Soundiiz](https://soundiiz.com/).
2. Connect your Apple Music as the **"Source"**.
3. Select **"Export to file"** (specifically CSV format) as the **"Destination"**.
4. Once downloaded, rename the file to exactly <code>library.csv</code> and place it in the Migratify folder. 
</details>

<details>
<summary><b style="font-size: 1.1em; color: #ff5500;">🎵 SoundCloud</b></summary>
<br>
SoundCloud closed off public API access years ago.

1. Visit [TuneMyMusic](https://www.tunemymusic.com/) or [Soundiiz](https://soundiiz.com/).
2. Connect your SoundCloud as the **"Source"**.
3. Select **CSV file** export as the **"Destination"**.
4. Rename the file to exactly <code>library.csv</code> and place it inside the Migratify folder.
</details>

---

## 🔑 Step 2: Destination Setup (Target)

Migratify needs authorized access to "Like" songs on your behalf. Expand your target destination below:

<details>
<summary><b style="font-size: 1.1em; color: #FF0000;">🎧 YouTube Music</b></summary>
<br>
We use header emulation to safely authorize without Google Cloud Console headaches.

1. Open [music.youtube.com](https://music.youtube.com/) and make sure you are logged in.
2. Open **Developer Tools** (Press `F12` or `Ctrl+Shift+I`).
3. Go to the **Network** tab.
4. Refresh the page or type anything in the YouTube Music search bar to populate some requests.
5. In the new list of requests, right-click any request named `browse` or `next`.
6. Select **Copy ➔ Copy as cURL (bash)**. *(Windows users: DO NOT choose cmd, pick bash!)*
7. Create a new text file named `headers.txt` in the Migratify script folder and paste the copied data inside. Save it.
</details>

---

## 🏎️ Step 3: Run Migration

Simply run the script:
```bash
python migrate.py
```
Follow the terminal prompts.

### ⚠️ Issue: "Session Expired / 401 Unauthorized"
YouTube Music can expire your browser tokens if it detects thousands of actions in a short period. If the script halts with a 401 Error:
1. It's okay! Your progress was saved to `progress.json`.
2. Go back to your browser, use YouTube Music for a second, and **Repeat Step 2** to grab a brand new `cURL` request block.
3. Replace the entire contents of your `headers.txt` with the new data.
4. **Delete the `oauth.json` file** in the script folder to force a token reload.
5. Relaunch the script. It will confidently ask to resume where it crashed!

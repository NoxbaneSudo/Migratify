import csv
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAILED_CSV_PATH = os.path.join(BASE_DIR, "failed_songs.csv")

def get_duration_sec(duration_str):
    if not duration_str: return None
    try:
        parts = str(duration_str).split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except: pass
    return None

def universal_csv_parser(filepath):
    songs = []
    if not os.path.exists(filepath):
        return songs
        
    try:
        with open(filepath, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return songs
                
            # Column mapping
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
    except Exception as e:
        print(f"Parser error: {e}")
        
    return songs

def log_failed_song(row_id, query, error):
    file_exists = os.path.exists(FAILED_CSV_PATH)
    try:
        with open(FAILED_CSV_PATH, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Row", "Query", "Error"])
            writer.writerow([row_id, query, error])
    except: pass

def parse_curl(raw_content):
    """
    Parses a cURL (bash) command and extracts headers for ytmusicapi.
    Returns: (raw_headers_string, error_message)
    """
    low_content = raw_content.lower()
    
    if low_content.startswith("http"):
        return None, "Error: You pasted a URL instead of a cURL command. Copy as 'cURL (bash)'."

    raw_headers_lines = []
    
    # Extract -H 'header: value'
    header_matches = re.findall(r"-H '([^']+)'", raw_content)
    header_matches += re.findall(r'-H "([^"]+)"', raw_content)
    for h in header_matches:
        raw_headers_lines.append(h)
    
    # Extract -b 'cookie_string'
    cookie_matches = re.findall(r"-b '([^']+)'", raw_content)
    cookie_matches += re.findall(r'-b "([^"]+)"', raw_content)
    for c in cookie_matches:
        raw_headers_lines.append(f"cookie: {c}")
        
    if not raw_headers_lines:
        # Check if it was already raw headers? 
        if "cookie:" in low_content:
            return raw_content, None
        return None, "Error: No headers found in cURL. Make sure to Copy as 'cURL (bash)'."

    # Verify cookie
    final_content = "\n".join(raw_headers_lines)
    if "cookie" not in final_content.lower():
        return None, "Error: Cookie header not found in the pasted cURL."
        
    # Inject x-goog-authuser if missing
    if "x-goog-authuser" not in final_content.lower():
        final_content += "\nx-goog-authuser: 0"
        
    return final_content, None

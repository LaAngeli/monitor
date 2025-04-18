import os
import time
import csv
from googleapiclient.discovery import build
from datetime import datetime

# -------------------- Configurare --------------------
# Introdu API Key-ul de la Google
API_KEY = 'AIzaSyAFSL8UzA7kCU1pafJiGz2kIyUEFyxq_lI'

# Introdu ID-ul videoclipului pe care vrei să-l monitorizezi
VIDEO_ID = '-v6fskQQan0'

# Intervalul de timp între verificări (în secunde). Exemplu: 60 secunde.
POLLING_INTERVAL = 60

# Numele fișierului CSV unde se vor stoca datele.
CSV_FILE = 'comment_evolution_data.csv'

# -------------------- Inițializare API YouTube --------------------
youtube = build('youtube', 'v3', developerKey=API_KEY)

# -------------------- Funcții helper --------------------
def initialize_csv(file_path):
    """
    Creează fișierul CSV cu antete, dacă nu există deja.
    Structura este: Timestamp, Comment_ID, Author, Text_Comentariu, Like_Count
    """
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Comment_ID', 'Author', 'Comment_Text', 'Like_Count'])

def fetch_comments(video_id, api_key, page_token=None):
    """
    Folosește YouTube API pentru a obține comentariile de pe videoclipul dat.
    Returnează o listă de comentarii și eventual un nextPageToken (dacă există).
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    try:
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=100,
            pageToken=page_token,
            order='time'  # Cele mai noi comentarii primele
        ).execute()
        
        comments = response.get('items', [])
        next_page_token = response.get('nextPageToken', None)
        return comments, next_page_token
    except Exception as e:
        print(f"Eroare la preluarea comentariilor: {str(e)}")
        return [], None

def log_comment_data(timestamp, comment_id, author, text, like_count):
    """
    Salvează o înregistrare în CSV. Pentru fiecare actualizare (fie comentariu nou sau update al like_count)
    se adaugă un rând nou cu timestampul actual.
    """
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, comment_id, author, text, like_count])

# -------------------- Funcția principală --------------------
def monitor_comments(video_id, api_key, log_callback=None, polling_interval=60, should_continue=None):
    """
    Monitorizează continuu comentariile:
    - Detectează comentariile noi
    - Urmărește evoluția numărului de like-uri
    - Se oprește când should_continue() returnează False
    """
    tracked_comments = {}  # key: comment_id, value: ultima valoare a like_count

    if log_callback:
        log_callback(f"Pornirea monitorizării pentru videoclipul: {video_id}")
    
    while should_continue and should_continue():  # Verifică dacă trebuie să continue monitorizarea
        try:
            # Obținem comentariile curente
            page_token = None
            all_comments = []
            
            # Verificăm din nou înainte de a începe colectarea comentariilor
            if not (should_continue and should_continue()):
                break
                
            while True:
                comments, page_token = fetch_comments(video_id, api_key, page_token)
                all_comments.extend(comments)
                if not page_token:
                    break
                    
                # Verificăm din nou după fiecare pagină de comentarii
                if not (should_continue and should_continue()):
                    return

            # Verificăm din nou înainte de a procesa comentariile
            if not (should_continue and should_continue()):
                break

            # Iterăm prin fiecare comentariu
            changes_detected = False
            for item in all_comments:
                # Verificăm starea înainte de a procesa fiecare comentariu
                if not (should_continue and should_continue()):
                    return
                    
                snippet = item['snippet']['topLevelComment']['snippet']
                comment_id = item['snippet']['topLevelComment']['id']
                author = snippet.get('authorDisplayName', 'Nedefinit')
                text = snippet.get('textDisplay', '')
                like_count = snippet.get('likeCount', 0)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if (comment_id not in tracked_comments) or (tracked_comments[comment_id] != like_count):
                    tracked_comments[comment_id] = like_count
                    log_comment_data(timestamp, comment_id, author, text, like_count)
                    if log_callback:
                        log_callback(f"[{timestamp}] ID: {comment_id} | Autor: {author} | Like-uri: {like_count}")
                    changes_detected = True

            # Verificăm starea înainte de a afișa mesajul final
            if should_continue and should_continue():
                # Afișăm mesaj de actualizare
                if log_callback:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if changes_detected:
                        log_callback(f"[{timestamp}] Verificare completă - S-au detectat modificări")
                    else:
                        log_callback(f"[{timestamp}] Verificare completă - Nu s-au detectat modificări")

            # Verificăm starea înainte de a aștepta
            if should_continue and should_continue():
                time.sleep(polling_interval)
            else:
                break
                
        except Exception as e:
            if log_callback and should_continue and should_continue():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_callback(f"[{timestamp}] Eroare: {str(e)}")
            if should_continue and should_continue():
                time.sleep(polling_interval)
            else:
                break

# -------------------- Execuția scriptului --------------------
if __name__ == '__main__':
    # Inițializează CSV-ul (dacă nu există deja)
    initialize_csv(CSV_FILE)
    
    # Pornirea monitorizării cu posibilitatea de a opri cu Ctrl+C
    try:
        monitor_comments(VIDEO_ID, API_KEY)
    except KeyboardInterrupt:
        print("Monitorizarea a fost oprită manual.")

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import threading
import os
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
from youtube_comment_monitor import monitor_comments

# Încărcăm variabilele de mediu
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

# Variabile globale pentru monitorizare
monitoring_thread = None
is_monitoring = False
monitored_comments = {}
log_messages = []

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'youtube_user'),
        password=os.getenv('DB_PASSWORD', 'Parola123!@#'),
        database=os.getenv('DB_NAME', 'youtube_monitor')
    )

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id VARCHAR(255) PRIMARY KEY,
            video_id VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            text TEXT NOT NULL,
            likes INT DEFAULT 0,
            first_seen DATETIME NOT NULL,
            last_updated DATETIME NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS likes_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            comment_id VARCHAR(255) NOT NULL,
            likes INT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (comment_id) REFERENCES comments(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def log_callback(message):
    timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    log_messages.append(f"{timestamp} {message}")
    if len(log_messages) > 1000:
        log_messages.pop(0)
    socketio.emit('log_update', {'message': f"{timestamp} {message}"})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_thread, is_monitoring
    
    if is_monitoring:
        return jsonify({'error': 'Monitorizarea este deja în curs'}), 400
    
    data = request.json
    video_id = data.get('video_id')
    api_key = data.get('api_key')
    
    if not video_id or not api_key:
        return jsonify({'error': 'Video ID și API Key sunt necesare'}), 400
    
    is_monitoring = True
    monitoring_thread = threading.Thread(
        target=monitor_comments,
        args=(video_id, api_key, log_callback),
        daemon=True
    )
    monitoring_thread.start()
    
    return jsonify({'message': 'Monitorizarea a început'})

@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global is_monitoring
    is_monitoring = False
    return jsonify({'message': 'Monitorizarea a fost oprită'})

@app.route('/api/get_logs')
def get_logs():
    return jsonify({'logs': log_messages})

@app.route('/api/search_logs')
def search_logs():
    search_term = request.args.get('q', '').lower()
    filtered_logs = [log for log in log_messages if search_term in log.lower()]
    return jsonify({'logs': filtered_logs})

@app.route('/api/get_stats')
def get_stats():
    return jsonify({
        'is_monitoring': is_monitoring,
        'monitored_comments_count': len(monitored_comments)
    })

if __name__ == '__main__':
    init_db()
    socketio.run(app, 
                host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 5000)),
                debug=os.getenv('DEBUG', 'False').lower() == 'true') 
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from datetime import datetime
from youtube_comment_monitor import monitor_comments, initialize_csv

# API Key implicit
DEFAULT_API_KEY = 'AIzaSyAFSL8UzA7kCU1pafJiGz2kIyUEFyxq_lI'

class YouTubeMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment Monitor")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Variabile
        self.is_monitoring = False
        self.monitor_thread = None
        self.start_time = None
        self.timer_id = None
        self.comments_count = 0
        self.changed_comments = {}  # Dicționar pentru a urmări comentariile modificate
        self.search_text = tk.StringVar()
        self.search_text.trace("w", self.filter_logs)
        
        # Stilizare
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#2196F3")
        self.style.configure("TLabel", padding=6)
        self.style.configure("TEntry", padding=6)
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Status.TLabel", font=("Arial", 10))
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="YouTube Comment Monitor", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        # Frame pentru input
        input_frame = ttk.LabelFrame(main_frame, text="Configurare Monitorizare", padding="10")
        input_frame.pack(fill=tk.X, pady=10)
        
        # Label și Entry pentru Video ID
        video_frame = ttk.Frame(input_frame)
        video_frame.pack(fill=tk.X, pady=5)
        
        video_label = ttk.Label(video_frame, text="Video ID:", width=15)
        video_label.pack(side=tk.LEFT, padx=5)
        
        self.video_entry = ttk.Entry(video_frame)
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Butoane
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Monitorizare", command=self.toggle_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Șterge Log-uri", command=self.clear_logs)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Frame pentru statistici
        stats_frame = ttk.LabelFrame(main_frame, text="Statistici", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # Timp de rulare
        ttk.Label(stats_grid, text="Timp de rulare:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.runtime_label = ttk.Label(stats_grid, text="00:00:00")
        self.runtime_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Număr de comentarii monitorizate
        ttk.Label(stats_grid, text="Comentarii monitorizate:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.comments_label = ttk.Label(stats_grid, text="0")
        self.comments_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Frame pentru log-uri și căutare
        log_frame = ttk.LabelFrame(main_frame, text="Log-uri", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame pentru căutare
        search_frame = ttk.Frame(log_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        search_label = ttk.Label(search_frame, text="Caută autor:")
        search_label.pack(side=tk.LEFT, padx=5)
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_text)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.search_button = ttk.Button(search_frame, text="Caută", command=self.perform_search)
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Text widget pentru log-uri
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Gata pentru monitorizare")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, style="Status.TLabel")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Inițializare CSV
        initialize_csv('comment_evolution_data.csv')
        
        # Variabile pentru statistici
        self.monitored_comments = set()
        self.start_time = None
        self.update_timer()
        
        # Configurare taste rapide
        self.setup_shortcuts()
        
        # Pornim timer-ul pentru actualizarea status bar-ului
        self.update_status_bar()

    def setup_shortcuts(self):
        # Ctrl+F pentru focus pe câmpul de căutare
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        
        # Enter în câmpul de căutare pentru a activa căutarea
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        
        # Ctrl+Enter pentru a porni/opri monitorizarea
        self.root.bind('<Control-Return>', lambda e: self.toggle_monitoring())
        
        # Ctrl+L pentru a șterge log-urile
        self.root.bind('<Control-l>', lambda e: self.clear_logs())
        
        # Escape pentru a ieși din câmpul de căutare
        self.search_entry.bind('<Escape>', lambda e: self.log_text.focus())
        
        # Configurare tag-uri pentru evidențiere
        self.log_text.tag_configure("search_highlight", background="yellow", foreground="black")
        self.log_text.tag_configure("likes", font=("Arial", 9, "bold"))
        self.log_text.tag_configure("verificare", font=("Arial", 9, "bold"), foreground="green")

    def update_status_bar(self):
        """Actualizează periodic status bar-ul"""
        if self.is_monitoring:
            self.status_var.set(f"Monitorizare în curs... ({len(self.monitored_comments)} comentarii)")
        self.root.after(2500, self.update_status_bar)

    def perform_search(self):
        search_term = self.search_text.get().strip()
        if search_term:
            self.filter_logs()
            # Afișează numărul de rezultate găsite
            count = self.count_search_results(search_term)
            if count > 0:
                self.status_var.set(f"Rezultate găsite: {count} pentru '{search_term}'")
            else:
                self.status_var.set(f"Niciun rezultat găsit pentru '{search_term}'")
        else:
            if self.is_monitoring:
                self.status_var.set(f"Monitorizare în curs... ({len(self.monitored_comments)} comentarii)")
            else:
                self.status_var.set("Gata pentru monitorizare")
            self.log_text.tag_remove("search_highlight", "1.0", tk.END)

    def count_search_results(self, search_term):
        count = 0
        start_pos = "1.0"
        while True:
            start_pos = self.log_text.search(f"Autor: {search_term}", start_pos, tk.END, nocase=True)
            if not start_pos:
                break
            count += 1
            start_pos = f"{start_pos}+1c"
        return count

    def update_timer(self):
        if self.is_monitoring and self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_timer)

    def log_message(self, message):
        # Verifică dacă mesajul conține "Verificare completă"
        if "Verificare completă" in message:
            # Adaugă mesajul de verificare cu tag-ul "verificare"
            self.log_text.insert(tk.END, message, "verificare")
            self.log_text.insert(tk.END, "\n")
        # Verifică dacă mesajul conține like-uri
        elif "like-uri:" in message:
            # Extrage părțile mesajului
            parts = message.split("like-uri:")
            before_likes = parts[0]
            likes_text = parts[1]
            
            # Adaugă textul dinainte de like-uri
            self.log_text.insert(tk.END, f"{before_likes}like-uri:", "normal")
            
            # Adaugă numărul de like-uri cu tag-ul "likes"
            self.log_text.insert(tk.END, likes_text, "likes")
            self.log_text.insert(tk.END, "\n")
        else:
            # Adaugă mesajul normal
            self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.see(tk.END)
        
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log-urile au fost șterse.")
        if self.is_monitoring:
            self.status_var.set(f"Monitorizare în curs... ({len(self.monitored_comments)} comentarii)")
        else:
            self.status_var.set("Gata pentru monitorizare")

    def toggle_monitoring(self):
        if not self.is_monitoring:
            video_id = self.video_entry.get().strip()
            
            if not video_id:
                messagebox.showerror("Eroare", "Vă rugăm să introduceți Video ID!")
                return
            
            self.is_monitoring = True
            self.start_button.config(text="Oprește Monitorizarea")
            self.status_var.set("Monitorizare în curs...")
            self.start_time = datetime.now()
            self.monitored_comments.clear()
            
            # Pornim monitorizarea într-un thread separat
            self.monitor_thread = threading.Thread(
                target=self.start_monitoring,
                args=(video_id,),
                daemon=True
            )
            self.monitor_thread.start()
        else:
            self.is_monitoring = False
            self.start_button.config(text="Start Monitorizare")
            self.status_var.set("Monitorizare oprită")
            self.log_message("Monitorizarea a fost oprită.")
            self.start_time = None

    def start_monitoring(self, video_id):
        try:
            def log_callback(message):
                if not self.is_monitoring:
                    return  # Nu mai procesăm mesaje dacă monitorizarea a fost oprită
                self.root.after(0, self.log_message, message)
                # Actualizăm numărul de comentarii monitorizate
                if "ID:" in message and "Autor:" in message:
                    comment_id = message.split("ID:")[1].split("|")[0].strip()
                    self.monitored_comments.add(comment_id)
                    self.root.after(0, lambda: self.comments_label.config(text=str(len(self.monitored_comments))))
                    self.root.after(0, lambda: self.status_var.set(f"Monitorizare în curs... ({len(self.monitored_comments)} comentarii)"))
            
            # Funcție pentru verificarea stării monitorizării
            def should_continue():
                return self.is_monitoring
            
            # Pornește monitorizarea cu verificarea stării
            monitor_comments(video_id, DEFAULT_API_KEY, log_callback, should_continue=should_continue)
            
        except Exception as e:
            if self.is_monitoring:  # Afișăm eroarea doar dacă monitorizarea este încă activă
                self.root.after(0, messagebox.showerror, "Eroare", str(e))
                self.root.after(0, self.toggle_monitoring)
                self.root.after(0, lambda: self.status_var.set("Eroare la monitorizare"))

    def filter_logs(self, *args):
        search_term = self.search_text.get().lower().strip()
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)
        
        if search_term:
            # Salvează poziția curentă a scroll-ului
            current_scroll = self.log_text.yview()
            
            # Caută și evidențiază
            start_pos = "1.0"
            while True:
                # Caută după "Autor: " urmat de termenul de căutare
                start_pos = self.log_text.search(f"Autor: {search_term}", start_pos, tk.END, nocase=True)
                if not start_pos:
                    break
                
                # Extrage linia completă
                line_start = self.log_text.index(f"{start_pos} linestart")
                line_end = self.log_text.index(f"{start_pos} lineend")
                line_text = self.log_text.get(line_start, line_end)
                
                # Evidențiază întreaga linie
                self.log_text.tag_add("search_highlight", line_start, line_end)
                
                # Continuă căutarea de la sfârșitul liniei
                start_pos = line_end
            
            # Restaurează poziția scroll-ului
            self.log_text.yview_moveto(current_scroll[0])
            
            # Dacă nu s-au găsit rezultate, afișează un mesaj
            if not self.log_text.tag_ranges("search_highlight"):
                self.status_var.set(f"Niciun rezultat găsit pentru '{search_term}'")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeMonitorGUI(root)
    root.mainloop() 
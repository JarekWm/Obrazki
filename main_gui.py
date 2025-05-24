import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
from config import ConfigManager
from file_manager import FileManager
from image_converter import ImageConverter
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess

class ImageConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Konwerter Obrazów")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # Inicjalizacja modułów
        self.config_manager = ConfigManager()
        self.file_manager = FileManager()
        self.converter = ImageConverter()
        
        # Wczytaj ustawienia
        self.settings = self.config_manager.load_settings()
        
        # Zmienne
        self.selected_files = []
        self.max_size_var = tk.StringVar(value=self.settings.get("max_size", ""))
        
        # Nowe zmienne dla dłuższej i krótszej krawędzi zamiast szerokości i wysokości
        self.longer_edge_var = tk.StringVar(value=self.settings.get("longer_edge", ""))
        self.shorter_edge_var = tk.StringVar(value=self.settings.get("shorter_edge", ""))
        
        self.suffix_var = tk.StringVar(value=self.settings.get("suffix", "_converted"))
        self.output_format_var = tk.StringVar(value=self.settings.get("output_format", "JPEG"))
        self.output_dir_var = tk.StringVar(value=self.settings.get("output_directory", ""))
        self.delete_originals_var = tk.BooleanVar(value=self.settings.get("delete_originals", False))
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # Tworzenie widgetów
        self.create_widgets()
        
    def create_widgets(self):
        # Frame dla plików z obsługą drag and drop
        file_frame = ttk.LabelFrame(self.root, text="Wybór plików")
        file_frame.pack(fill="x", padx=10, pady=10, ipady=5)
        
        # Przycisk wyboru plików
        select_btn = ttk.Button(file_frame, text="Wybierz pliki obrazów", command=self.select_files)
        select_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Lista wybranych plików
        self.file_listbox = tk.Listbox(file_frame, height=4)
        self.file_listbox.pack(side=tk.LEFT, padx=10, pady=5, fill="x", expand=True)
        
        # Scrollbar dla listy plików
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0,10))
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # Obszar do przeciągania i upuszczania
        drop_frame = ttk.LabelFrame(self.root, text="Przeciągnij i upuść pliki obrazów tutaj")
        drop_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label wewnątrz drop_frame do łatwiejszego przeciągnięcia
        drop_label = ttk.Label(drop_frame, text="Upuść pliki obrazów tutaj", anchor="center")
        drop_label.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Konfiguracja obsługi przeciągania i upuszczania
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Frame dla opcji konwersji
        options_frame = ttk.LabelFrame(self.root, text="Opcje konwersji")
        options_frame.pack(fill="x", padx=10, pady=10, ipady=5)
        
        # Format wyjściowy
        ttk.Label(options_frame, text="Format wyjściowy:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        format_combo = ttk.Combobox(options_frame, textvariable=self.output_format_var, 
                                   values=self.converter.get_available_formats(), 
                                   state="readonly", width=10)
        format_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Maksymalny rozmiar
        ttk.Label(options_frame, text="Maksymalny rozmiar (KB):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(options_frame, textvariable=self.max_size_var, width=10).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Info o limitach rozmiaru
        ttk.Label(options_frame, text="(tylko dla JPEG i WebP)").grid(row=1, column=2, padx=0, pady=5, sticky="w")
        
        # Nowa rozdzielczość oparta na dłuższej i krótszej krawędzi
        ttk.Label(options_frame, text="Nowa rozdzielczość:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        resolution_frame = ttk.Frame(options_frame)
        resolution_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Podział na etykiety i pola wprowadzania dla dłuższej i krótszej krawędzi
        edge_frame1 = ttk.Frame(resolution_frame)
        edge_frame1.pack(fill="x", pady=2)
        ttk.Label(edge_frame1, text="Dłuższa krawędź:").pack(side=tk.LEFT)
        ttk.Entry(edge_frame1, textvariable=self.longer_edge_var, width=6).pack(side=tk.LEFT, padx=5)
        
        edge_frame2 = ttk.Frame(resolution_frame)
        edge_frame2.pack(fill="x", pady=2)
        ttk.Label(edge_frame2, text="Krótsza krawędź:").pack(side=tk.LEFT)
        ttk.Entry(edge_frame2, textvariable=self.shorter_edge_var, width=6).pack(side=tk.LEFT, padx=5)
        
        # Informacja o proporcjonalnej rozdzielczości
        ttk.Label(options_frame, text="(możesz podać tylko jedną wartość)").grid(row=2, column=3, padx=0, pady=5, sticky="w")
        
        # Sufiks
        ttk.Label(options_frame, text="Sufiks nazwy pliku:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(options_frame, textvariable=self.suffix_var).grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Katalog wyjściowy
        ttk.Label(options_frame, text="Katalog wyjściowy:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        dir_entry = ttk.Entry(options_frame, textvariable=self.output_dir_var, width=40)
        dir_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="we")
        
        dir_buttons_frame = ttk.Frame(options_frame)
        dir_buttons_frame.grid(row=4, column=3, padx=(0, 10), pady=5, sticky="w")
        
        browse_btn = ttk.Button(dir_buttons_frame, text="Przeglądaj...", command=self.select_output_directory)
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        open_dir_btn = ttk.Button(dir_buttons_frame, text="Otwórz katalog", command=self.open_output_directory)
        open_dir_btn.pack(side=tk.LEFT)
        
        options_frame.columnconfigure(1, weight=1)  # Aby pole entry się rozciągało
        
        # Opcja usuwania oryginalnych plików
        delete_check = ttk.Checkbutton(options_frame, text="Usuń oryginalne pliki po udanej konwersji", variable=self.delete_originals_var)
        delete_check.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        
        # Frame dla przycisków akcji
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        # Przyciski
        ttk.Button(action_frame, text="Zapisz ustawienia", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Konwertuj", command=self.start_conversion).pack(side=tk.RIGHT, padx=5)
        
        # Pasek postępu
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=630, mode="determinate", variable=self.progress_var)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        # Log działań
        log_frame = ttk.LabelFrame(self.root, text="Log Działań")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)

        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
    
    def log_message(self, message):
        """Dodaje wiadomość do pola logu."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Automatyczne przewijanie do końca
        self.log_text.config(state=tk.DISABLED)

    def handle_drop(self, event):
        """Obsługa upuszczonych plików"""
        files = self.parse_drop_data(event.data)
        # Filtruj obsługiwane formaty plików
        accepted_extensions = ('.heic', '.png', '.jpg', '.jpeg')
        image_files = [f for f in files if f.lower().endswith(accepted_extensions)]
        
        if image_files:
            # Limit do 5 plików
            files_to_add = image_files[:5]
            if len(image_files) > 5:
                messagebox.showwarning("Limit plików", "Wybrano więcej niż 5 plików. Tylko pierwsze 5 zostanie dodanych.")
            
            self.selected_files = files_to_add
            self.file_listbox.delete(0, tk.END)
            for file in files_to_add:
                self.file_listbox.insert(tk.END, os.path.basename(file))
            
            loaded_filenames = [os.path.basename(f) for f in files_to_add]
            self.log_message(f"Dodano pliki ({len(loaded_filenames)}): {', '.join(loaded_filenames)}")
        else:
            messagebox.showwarning("Ostrzeżenie", "Nie upuszczono obsługiwanych plików obrazów (HEIC, PNG, JPG, JPEG)")
    
    def parse_drop_data(self, data):
        """Parsuje dane upuszczonych plików"""
        # Dane są w różnym formacie w zależności od systemu operacyjnego
        files = []
        for item in data.split():
            item = item.strip()
            # Usuń znaki {} jeśli istnieją (Windows często tak zwraca)
            if item.startswith('{') and item.endswith('}'):
                item = item[1:-1]
            # Usuń znaki cudzysłowu jeśli istnieją
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            # Upewnij się, że to ścieżka do istniejącego pliku
            if os.path.isfile(item):
                files.append(item)
        return files
        
    def select_files(self):
        filetypes = (
            ("Pliki obrazów", "*.heic *.HEIC *.png *.jpg *.jpeg"),
            ("Pliki HEIC", "*.heic *.HEIC"),
            ("Pliki PNG", "*.png"),
            ("Pliki JPEG", "*.jpg *.jpeg"),
            ("Wszystkie pliki", "*.*")
        )
        files = filedialog.askopenfilenames(title="Wybierz pliki obrazów", filetypes=filetypes)
        
        if files:
            # Limit do 5 plików
            files_to_add = files[:5]
            if len(files) > 5:
                messagebox.showwarning("Limit plików", "Wybrano więcej niż 5 plików. Tylko pierwsze 5 zostanie dodanych.")
            
            self.selected_files = files_to_add
            self.file_listbox.delete(0, tk.END)
            for file in files_to_add:
                self.file_listbox.insert(tk.END, os.path.basename(file))
            
            loaded_filenames = [os.path.basename(f) for f in files_to_add]
            self.log_message(f"Dodano pliki ({len(loaded_filenames)}): {', '.join(loaded_filenames)}")
        
    def select_output_directory(self):
        """Otwiera dialog wyboru katalogu i aktualizuje pole."""
        directory = filedialog.askdirectory(title="Wybierz katalog wyjściowy")
        if directory:  # Jeśli użytkownik wybrał katalog, a nie anulował
            self.output_dir_var.set(directory)
            self.log_message(f"Ustawiono katalog wyjściowy: {directory}")
    
    def open_output_directory(self):
        """Otwiera katalog wyjściowy w Eksploratorze plików."""
        directory = self.output_dir_var.get()
        
        if not directory:
            self.log_message("Nie ustawiono katalogu wyjściowego.")
            return
            
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                self.log_message(f"Utworzono katalog wyjściowy: {directory}")
            except Exception as e:
                self.log_message(f"Nie można utworzyć katalogu wyjściowego: {str(e)}")
                return
        
        try:
            # Otwórz katalog w domyślnym eksploratorze plików
            if os.name == 'nt':  # Windows
                os.startfile(directory)
            elif os.name == 'posix':  # macOS, Linux
                if os.path.exists('/usr/bin/open'):  # macOS
                    subprocess.Popen(['open', directory])
                else:  # Linux
                    subprocess.Popen(['xdg-open', directory])
            self.log_message(f"Otwarto katalog wyjściowy: {directory}")
        except Exception as e:
            self.log_message(f"Błąd przy otwieraniu katalogu: {str(e)}")
        
    def save_settings(self):
        settings = {
            "max_size": self.max_size_var.get(),
            "longer_edge": self.longer_edge_var.get(),
            "shorter_edge": self.shorter_edge_var.get(),
            "suffix": self.suffix_var.get(),
            "output_format": self.output_format_var.get(),
            "output_directory": self.output_dir_var.get(),
            "delete_originals": self.delete_originals_var.get()
        }
        
        self.config_manager.save_settings(settings)
        messagebox.showinfo("Informacja", "Ustawienia zostały zapisane")
        
    def calculate_dimensions(self, original_width, original_height):
        """
        Oblicza nowe wymiary obrazu na podstawie ustawień dłuższej i krótszej krawędzi
        
        Args:
            original_width (int): Oryginalna szerokość obrazu
            original_height (int): Oryginalna wysokość obrazu
            
        Returns:
            tuple: (nowa_szerokość, nowa_wysokość) lub None jeśli nie ustawiono wymiarów
        """
        longer_edge = self.longer_edge_var.get()
        shorter_edge = self.shorter_edge_var.get()
        
        # Określ, która krawędź jest dłuższa, a która krótsza w oryginalnym obrazie
        if original_width >= original_height:
            original_longer = original_width
            original_shorter = original_height
            is_landscape = True
        else:
            original_longer = original_height
            original_shorter = original_width
            is_landscape = False
        
        # Oblicz współczynnik proporcji
        aspect_ratio = original_longer / original_shorter
        
        # Przetwarzanie wartości wejściowych
        longer_edge_val = int(longer_edge) if longer_edge and longer_edge.isdigit() else None
        shorter_edge_val = int(shorter_edge) if shorter_edge and shorter_edge.isdigit() else None
        
        # Obliczanie nowych wymiarów
        if longer_edge_val and shorter_edge_val:
            # Obie wartości są określone - używamy ich bezpośrednio
            new_longer = longer_edge_val
            new_shorter = shorter_edge_val
        elif longer_edge_val:
            # Tylko dłuższa krawędź jest określona
            new_longer = longer_edge_val
            new_shorter = int(new_longer / aspect_ratio)
        elif shorter_edge_val:
            # Tylko krótsza krawędź jest określona
            new_shorter = shorter_edge_val
            new_longer = int(new_shorter * aspect_ratio)
        else:
            # Żadna wartość nie jest określona
            return None
            
        # Konwersja z powrotem na szerokość i wysokość
        if is_landscape:
            return (new_longer, new_shorter)
        else:
            return (new_shorter, new_longer)
        
    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Ostrzeżenie", "Nie wybrano plików do konwersji")
            return
        
        # Pobieranie ustawień
        max_size = self.max_size_var.get()
        if max_size and max_size.isdigit():
            max_size = int(max_size)
        else:
            max_size = None
            
        suffix = self.suffix_var.get()
        output_format = self.output_format_var.get()
        output_dir = self.output_dir_var.get()
        
        # Sprawdź i utwórz katalog wyjściowy, jeśli podano
        if output_dir:
            try:
                if self.file_manager.ensure_directory_exists(output_dir):
                    self.log_message(f"Katalog wyjściowy '{output_dir}' istnieje lub został utworzony.")
                else:
                    self.log_message(f"OSTRZEŻENIE: Nie można zweryfikować/utworzyć katalogu wyjściowego '{output_dir}'. Pliki będą zapisywane w katalogach źródłowych.")
                    output_dir = None
            except Exception as e:
                self.log_message(f"BŁĄD tworzenia katalogu wyjściowego '{output_dir}': {e}. Pliki będą zapisywane w katalogach źródłowych.")
                output_dir = None
        
        # Konwersja plików
        self.progress_var.set(0)
        total_files = len(self.selected_files)
        converted_files = 0
        
        # Wyczyść log przed rozpoczęciem
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.log_message("Rozpoczęto proces konwersji...")
        
        for i, heic_path in enumerate(self.selected_files):
            try:
                output_file = self.file_manager.generate_output_filename(
                    heic_path, 
                    output_format, 
                    suffix,
                    output_directory=output_dir
                )
                self.log_message(f"Konwertowanie: {os.path.basename(heic_path)}...")
                self.root.update_idletasks()
                
                # Otwieramy obraz do sprawdzenia jego wymiarów
                with Image.open(heic_path) as img:
                    orig_width, orig_height = img.size
                    
                    # Obliczenie nowych wymiarów
                    new_dimensions = self.calculate_dimensions(orig_width, orig_height)
                
                self.converter.convert_heic_to_format(
                    heic_path, 
                    output_file,
                    output_format=output_format,
                    max_size_kb=max_size, 
                    new_resolution=new_dimensions
                )
                
                self.log_message(f" -> Zapisano jako: {os.path.basename(output_file)}")
                
                # Usuń oryginalny plik, jeśli opcja jest włączona
                if self.delete_originals_var.get():
                    try:
                        os.remove(heic_path)
                        self.log_message(f"   Usunięto oryginał: {os.path.basename(heic_path)}")
                    except OSError as e:
                        self.log_message(f"   BŁĄD: Nie można usunąć oryginału {os.path.basename(heic_path)}: {e}")
                
                # Aktualizacja postępu
                converted_files += 1
                progress_value = ((i + 1) / total_files) * 100
                self.progress_var.set(progress_value)
                self.root.update_idletasks()
                
            except Exception as e:
                self.log_message(f"BŁĄD konwersji pliku {os.path.basename(heic_path)}: {str(e)}")
        
        self.log_message(f"Konwersja zakończona. Przekonwertowano {converted_files} z {total_files} plików.")
        self.progress_var.set(0) 
import os
import sys
import subprocess
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QFrame, 
                            QProgressBar, QTextEdit, QComboBox, QLineEdit, QCheckBox,
                            QGridLayout, QGroupBox, QSplitter, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl, QSize, QByteArray
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from config import ConfigManager
from file_manager import FileManager
from image_converter import ImageConverter

class DropArea(QLabel):
    """Obszar do przeciągania i upuszczania plików"""
    filesDropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ImageDropArea") # Ustawienie objectName dla specyficzności QSS
        self.setText("Upuść pliki obrazów tutaj")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(100)
        # self.setFrameShape(QFrame.Shape.StyledPanel) # QSS będzie kontrolować ramkę
        self.setAcceptDrops(True)
        
        self.original_style_sheet = "QLabel#ImageDropArea { border: 2px dashed #aaa; border-radius: 5px; color: #555; background-color: #f9f9f9; }"
        self.setStyleSheet(self.original_style_sheet)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("QLabel#ImageDropArea { border: 2px dashed #0078d7; border-radius: 5px; color: #333; background-color: #e6f2ff; }")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Przywraca styl po opuszczeniu obszaru przez kursor."""
        self.setStyleSheet(self.original_style_sheet) # Przywróć oryginalny styl
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self.original_style_sheet) # Przywróć oryginalny styl po upuszczeniu
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    file_paths.append(path)
            self.filesDropped.emit(file_paths)
            event.accept()
        else:
            event.ignore()

class ImageConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inicjalizacja modułów
        self.config_manager = ConfigManager()
        self.file_manager = FileManager()
        self.converter = ImageConverter()
        
        # Wczytaj ustawienia
        self.settings = self.config_manager.load_settings()
        
        # Zmienne
        self.selected_files = []
        
        # Ustawienia okna
        self.setWindowTitle("Konwerter Obrazów")
        self.setMinimumSize(700, 650) # Ustaw minimalny rozmiar najpierw

        geometry_restored = False
        if "window_geometry" in self.settings and self.settings["window_geometry"]:
            try:
                if self.restoreGeometry(QByteArray.fromBase64(self.settings["window_geometry"].encode('utf-8'))):
                    # self.log_message("Odtworzono rozmiar i pozycję okna.") # Log message będzie dodany później, gdy log_text będzie dostępne
                    geometry_restored = True
                else:
                    # self.log_message("Nie udało się odtworzyć geometrii okna (restoreGeometry zwróciło False).")
                    pass # Log message będzie dodany później
            except Exception as e:
                # self.log_message(f"Błąd podczas odtwarzania geometrii okna: {e}")
                pass # Log message będzie dodany później

        if not geometry_restored:
            # self.log_message("Ustawianie domyślnego rozmiaru okna.") # Log message będzie dodany później
            self.resize(750, 700) # Ustaw nieco większy domyślny rozmiar dla lepszego pierwszego wrażenia
        
        # Utwórz GUI
        self.create_widgets() # self.log_text jest tworzone tutaj
        
        # Załaduj zapisane ustawienia do kontrolek
        self.load_settings_to_ui()

        # Teraz można logować, bo self.log_text istnieje
        if "window_geometry" in self.settings and self.settings["window_geometry"]:
            if geometry_restored:
                 self.log_message("Odtworzono rozmiar i pozycję okna.")
            else: # Tutaj można zalogować błędy, jeśli restoreGeometry zwróciło False lub był wyjątek
                if not self.restoreGeometry(QByteArray.fromBase64(self.settings["window_geometry"].encode('utf-8'))):
                     self.log_message("Nie udało się odtworzyć geometrii okna (restoreGeometry zwróciło False) po utworzeniu widgetów.")
                # Błędy z exception są trudniejsze do złapania tutaj ponownie bez duplikacji kodu
        elif not geometry_restored : # Jeśli nie było geometrii lub jeśli odtworzenie nie powiodło się wcześniej
            self.log_message("Ustawiono domyślny rozmiar okna (750x700).")
            
        self.apply_app_styles()

    def toggle_options_visibility(self, is_checked):
        """Pokazuje lub ukrywa kontener opcji w zależności od stanu checkboxa QGroupBox."""
        self.options_container_widget.setVisible(is_checked)

    def apply_app_styles(self):
        qss_style_string = """
        QGroupBox { 
            margin-top: 1ex; /* Odstęp od góry dla tytułu */
            font-weight: bold; 
            border: 1px solid #ccc; /* Subtelne obramowanie dla groupboxa */
            border-radius: 5px;
            padding-top: 1.5ex; /* Dodatkowy padding, aby tytuł nie nachodził na zawartość */
        }
        QGroupBox::title { 
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px; /* Padding wokół tekstu tytułu */
            left: 10px; /* Odsunięcie tytułu od lewej krawędzi */
            background-color: #f0f0f0; /* Lekkie tło dla tytułu, aby "wystawał" z ramki */
            border-radius: 3px;
        }
        QPushButton { 
            padding: 6px 12px; /* Większy padding */
            border: 1px solid #ccc;
            border-radius: 4px; 
            background-color: #f0f0f0; /* Domyślny kolor tła */
            color: #333; /* Kolor tekstu */
        }
        QPushButton:hover {
            background-color: #e9e9e9; /* Jaśniejszy przy najechaniu */
            border-color: #adadad;
        }
        QPushButton:pressed {
            background-color: #dcdcdc; /* Ciemniejszy przy wciśnięciu */
            border-color: #999;
        }
        QLineEdit, QComboBox, QTextEdit, QListWidget { 
            padding: 4px; 
            border-radius: 4px; 
            border: 1px solid #ccc;
        }
        QComboBox::drop-down {
            border-left: 1px solid #ccc; /* Linia oddzielająca strzałkę */
            border-top-right-radius: 3px; /* Zaokrąglenie pasujące do widgetu */
            border-bottom-right-radius: 3px;
        }
        QComboBox::down-arrow {
            /* Można tu wstawić własną ikonę strzałki, jeśli standardowa nie pasuje */
            /* image: url(path/to/your/arrow-down.png); */
            /* width: 12px; */
            /* height: 12px; */
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center; /* Tekst procentowy na środku */
        }
        QProgressBar::chunk {
            background-color: #0078d7; /* Kolor paska postępu */
            border-radius: 3px; /* Lekkie zaokrąglenie samego paska */
        }
        """
        self.setStyleSheet(qss_style_string)

    def load_settings_to_ui(self):
        """Załaduj ustawienia z pliku do kontrolek UI"""
        self.max_size_input.setText(self.settings.get("max_size", ""))
        self.longer_edge_input.setText(self.settings.get("longer_edge", ""))
        self.shorter_edge_input.setText(self.settings.get("shorter_edge", ""))
        self.suffix_input.setText(self.settings.get("suffix", "_converted"))
        
        # Znajdź indeks formatu w comboboxie
        format_index = self.format_combo.findText(self.settings.get("output_format", "JPEG"))
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)
            
        self.output_dir_input.setText(self.settings.get("output_directory", ""))
        self.delete_originals_check.setChecked(self.settings.get("delete_originals", False))
        self.strip_metadata_check.setChecked(self.settings.get("strip_metadata", False))
        self.webp_lossless_check.setChecked(self.settings.get("webp_lossless", False))
        self.number_output_files_check.setChecked(self.settings.get("number_output_files", False))
        
        # Wczytaj i zastosuj stan zwinięcia QGroupBox "Opcje konwersji"
        options_expanded = self.settings.get('options_group_expanded', True) # Domyślnie rozwinięte
        self.options_group.setChecked(options_expanded)
        # Bezpośrednie ustawienie widoczności kontenera, ponieważ toggle_options_visibility jest podłączone do sygnału toggled,
        # a setChecked programistycznie niekoniecznie emituje ten sygnał w taki sam sposób jak kliknięcie użytkownika
        # (lub chcemy uniknąć potencjalnego podwójnego wywołania lub problemów z timingiem).
        self.options_container_widget.setVisible(options_expanded)

        # Upewnij się, że stan checkboxa WebP lossless jest poprawny po załadowaniu
        self.update_webp_lossless_check_state()
    
    def create_widgets(self):
        """Utwórz wszystkie widgety interfejsu użytkownika"""
        # Centralny widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # ==== SEKCJA WYBORU PLIKÓW ====
        file_group = QGroupBox("Wybór plików")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)
        
        # Przycisk wyboru plików i lista
        file_header_layout = QHBoxLayout()
        select_btn = QPushButton("Wybierz pliki obrazów")
        select_btn.clicked.connect(self.select_files)
        file_header_layout.addWidget(select_btn)
        file_header_layout.addStretch()
        file_layout.addLayout(file_header_layout)
        
        # Lista wybranych plików - teraz w trybie wielokolumnowym IconMode
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListWidget.ViewMode.IconMode)      # Powrót do IconMode
        self.file_list.setFlow(QListWidget.Flow.LeftToRight)       # Przepływ od lewej do prawej
        self.file_list.setWrapping(True)                           # Zawijanie elementów
        self.file_list.setIconSize(QSize(16, 16))                  # Małe ikony
        self.file_list.setGridSize(QSize(200, 40))                 # Rozmiar komórki (szerokość, wysokość)
        # self.file_list.setWordWrap(True) # Ta właściwość QListWidget nie kontroluje zawijania tekstu w QListWidgetItem w IconMode
        
        # Właściwości dla IconMode
        self.file_list.setResizeMode(QListWidget.ResizeMode.Adjust) # Dostosuj układ przy zmianie rozmiaru
        self.file_list.setMovement(QListWidget.Movement.Static)    # Elementy nieprzesuwalne

        file_layout.addWidget(self.file_list)
        
        # Obszar do przeciągania i upuszczania
        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.handle_dropped_files)
        file_layout.addWidget(self.drop_area)
        
        # main_layout.addWidget(file_group) # Zostanie dodane do splittera
        
        # ==== SEKCJA OPCJI KONWERSJI ====
        self.options_group = QGroupBox("Opcje konwersji") # Zmieniono na self.options_group
        self.options_group.setCheckable(True) # Umożliwia zwijanie
        
        # Kontener na wszystkie opcje wewnątrz QGroupBox
        self.options_container_widget = QWidget()
        options_layout = QGridLayout(self.options_container_widget) # Istniejący layout przypisany do kontenera
        # self.options_container_widget.setLayout(options_layout) # Już zrobione przez konstruktor QGridLayout

        # Główny layout dla QGroupBox, który będzie zawierał kontener
        options_group_main_layout = QVBoxLayout(self.options_group) # Layout dla self.options_group
        options_group_main_layout.addWidget(self.options_container_widget)
        # self.options_group.setLayout(options_group_main_layout) # Już zrobione przez konstruktor QVBoxLayout
        
        self.options_group.toggled.connect(self.toggle_options_visibility)

        # Format wyjściowy
        options_layout.addWidget(QLabel("Format wyjściowy:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.converter.get_available_formats())
        options_layout.addWidget(self.format_combo, 0, 1)

        # Opcja WebP lossless
        self.webp_lossless_check = QCheckBox("WebP bezstratny")
        options_layout.addWidget(self.webp_lossless_check, 0, 2) # Obok formatu
        self.format_combo.currentTextChanged.connect(self.update_webp_lossless_check_state)
        self.update_webp_lossless_check_state() # Ustaw stan początkowy zaraz po utworzeniu widgetu
        
        # Maksymalny rozmiar
        options_layout.addWidget(QLabel("Maksymalny rozmiar (KB):"), 1, 0)
        self.max_size_input = QLineEdit()
        options_layout.addWidget(self.max_size_input, 1, 1)
        options_layout.addWidget(QLabel("(tylko dla JPEG i WebP)"), 1, 2)
        
        # Rozdzielczość - dłuższa krawędź
        options_layout.addWidget(QLabel("Dłuższa krawędź:"), 2, 0)
        self.longer_edge_input = QLineEdit()
        options_layout.addWidget(self.longer_edge_input, 2, 1)
        
        # Rozdzielczość - krótsza krawędź
        options_layout.addWidget(QLabel("Krótsza krawędź:"), 3, 0)
        self.shorter_edge_input = QLineEdit()
        options_layout.addWidget(self.shorter_edge_input, 3, 1)
        options_layout.addWidget(QLabel("(możesz podać tylko jedną wartość)"), 3, 2)
        
        # Sufiks
        options_layout.addWidget(QLabel("Sufiks nazwy pliku:"), 4, 0)
        self.suffix_input = QLineEdit()
        options_layout.addWidget(self.suffix_input, 4, 1, 1, 2)
        
        # Katalog wyjściowy
        options_layout.addWidget(QLabel("Katalog wyjściowy:"), 5, 0)
        self.output_dir_input = QLineEdit()
        options_layout.addWidget(self.output_dir_input, 5, 1, 1, 2)
        
        dir_buttons_layout = QHBoxLayout()
        browse_btn = QPushButton("Przeglądaj...")
        browse_btn.clicked.connect(self.select_output_directory)
        open_dir_btn = QPushButton("Otwórz katalog")
        open_dir_btn.clicked.connect(self.open_output_directory)
        
        dir_buttons_layout.addWidget(browse_btn)
        dir_buttons_layout.addWidget(open_dir_btn)
        dir_buttons_layout.addStretch()
        
        options_layout.addLayout(dir_buttons_layout, 5, 3)
        
        # Opcja usuwania oryginałów
        self.delete_originals_check = QCheckBox("Usuń oryginalne pliki po udanej konwersji")
        options_layout.addWidget(self.delete_originals_check, 6, 0, 1, 3) # Zmieniono span na 3
        
        # Opcja usuwania metadanych
        self.strip_metadata_check = QCheckBox("Usuń metadane (EXIF, ICC, etc.)")
        options_layout.addWidget(self.strip_metadata_check, 7, 0, 1, 3)
        
        # Opcja numerowania plików wynikowych
        self.number_output_files_check = QCheckBox("Numeruj pliki wynikowe (np. 01_nazwa.jpg)")
        options_layout.addWidget(self.number_output_files_check, 8, 0, 1, 3)

        # main_layout.addWidget(options_group) # Zostanie dodane do splittera
        
        # ==== PRZYCISKI AKCJI ====
        action_layout = QHBoxLayout()
        save_settings_btn = QPushButton("Zapisz ustawienia")
        save_settings_btn.clicked.connect(self.save_settings)
        action_layout.addWidget(save_settings_btn)
        
        action_layout.addStretch()
        
        convert_btn = QPushButton("Konwertuj")
        convert_btn.clicked.connect(self.start_conversion)
        action_layout.addWidget(convert_btn)
        
        # main_layout.addLayout(action_layout) # Zostanie dodane do top_layout w splitterze
        
        # ==== PASEK POSTĘPU ====
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        # main_layout.addWidget(self.progress_bar) # Zostanie dodane do top_layout w splitterze
        
        # ==== LOG DZIAŁAŃ ====
        log_group = QGroupBox("Log Działań")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # main_layout.addWidget(log_group) # Zostanie dodane do splittera

        # ==== Konfiguracja Splittera ====
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Górny panel dla file_group, options_group, action_layout, progress_bar
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(file_group)
        top_layout.addWidget(self.options_group) # Użyj self.options_group
        top_layout.addLayout(action_layout)
        top_layout.addWidget(self.progress_bar)
        # top_widget.setLayout(top_layout) # Niepotrzebne, konstruktor QVBoxLayout już to robi

        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(log_group) # log_group bezpośrednio do splittera

        # Ustawienie początkowych rozmiarów splittera (dostosuj wartości wg potrzeb)
        # Można użyć proporcji okna, ale na start stałe wartości mogą być łatwiejsze
        # self.resize(700, 650) # Zakładając, że to jest rozmiar okna
        main_splitter.setSizes([400, 250]) # Daje więcej miejsca górnemu panelowi

        # Dodaj główny splitter do main_layout
        main_layout.addWidget(main_splitter)
        
        # Usuń stare ustawienia stretch, QSplitter zarządza tym teraz
        # main_layout.setStretch(0, 3)
        # main_layout.setStretch(1, 0)
        # main_layout.setStretch(3, 0)
        # main_layout.setStretch(4, 2)

    def update_webp_lossless_check_state(self, current_format_text=None):
        """Aktualizuje stan checkboxa WebP lossless na podstawie wybranego formatu."""
        if current_format_text is None:
            current_format_text = self.format_combo.currentText()
        
        if current_format_text == "WebP":
            self.webp_lossless_check.setEnabled(True)
        else:
            self.webp_lossless_check.setEnabled(False)
            self.webp_lossless_check.setChecked(False) # Odznacz, jeśli nie WebP
    
    def log_message(self, message):
        """Dodaje wiadomość do pola logu."""
        self.log_text.append(message)
    
    def select_files(self):
        """Otwiera okno dialogowe wyboru plików."""
        file_filter = (
            "Pliki obrazów (*.heic *.HEIC *.png *.jpg *.jpeg);;Pliki HEIC (*.heic *.HEIC);;"
            "Pliki PNG (*.png);;Pliki JPEG (*.jpg *.jpeg);;Wszystkie pliki (*)"
        )
        files, _ = QFileDialog.getOpenFileNames(
            self, "Wybierz pliki obrazów", "", file_filter
        )
        
        if files:
            self.process_selected_files(files)
    
    def handle_dropped_files(self, files):
        """Obsługuje upuszczone pliki."""
        # Filtruj obsługiwane formaty plików
        accepted_extensions = ('.heic', '.png', '.jpg', '.jpeg')
        image_files = [f for f in files if os.path.splitext(f.lower())[1] in accepted_extensions]
        
        if image_files:
            self.process_selected_files(image_files)
        else:
            QMessageBox.warning(
                self, "Ostrzeżenie", 
                "Nie upuszczono obsługiwanych plików obrazów (HEIC, PNG, JPG, JPEG)"
            )
    
    def process_selected_files(self, files):
        """Przetwarzanie wybranych plików (bez limitu)."""
        # Nie ma już limitu, więc bierzemy wszystkie pliki
        files_to_add = files 
        
        self.selected_files = files_to_add
        self.file_list.clear()
        
        # Import QStyle wewnątrz metody, aby uniknąć problemów z importem na poziomie modułu, jeśli nie jest używane
        from PyQt6.QtWidgets import QStyle, QListWidgetItem

        for file_path in files_to_add:
            item = QListWidgetItem(os.path.basename(file_path))
            # Użyj standardowej ikony pliku
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            item.setIcon(icon)
            self.file_list.addItem(item)
        
        loaded_filenames = [os.path.basename(f) for f in files_to_add]
        self.log_message(f"Dodano pliki ({len(loaded_filenames)}): {', '.join(loaded_filenames)}")
    
    def select_output_directory(self):
        """Otwiera dialog wyboru katalogu wyjściowego."""
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog wyjściowy", 
            self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
            self.log_message(f"Ustawiono katalog wyjściowy: {directory}")
    
    def open_output_directory(self):
        """Otwiera katalog wyjściowy w Eksploratorze plików."""
        directory = self.output_dir_input.text()
        
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
        """Zapisuje ustawienia do pliku konfiguracyjnego."""
        settings = {
            "max_size": self.max_size_input.text(),
            "longer_edge": self.longer_edge_input.text(),
            "shorter_edge": self.shorter_edge_input.text(),
            "suffix": self.suffix_input.text(),
            "output_format": self.format_combo.currentText(),
            "output_directory": self.output_dir_input.text(),
            "delete_originals": self.delete_originals_check.isChecked(),
            "strip_metadata": self.strip_metadata_check.isChecked(),
            "webp_lossless": self.webp_lossless_check.isChecked(),
            "number_output_files": self.number_output_files_check.isChecked()
        }
        
        # Zapisz geometrię okna
        settings["window_geometry"] = self.saveGeometry().toBase64().data().decode('utf-8')
        # Zapisz stan zwinięcia QGroupBox "Opcje konwersji"
        settings['options_group_expanded'] = self.options_group.isChecked()
        
        self.config_manager.save_settings(settings)
        QMessageBox.information(self, "Informacja", "Ustawienia zostały zapisane")
    
    def calculate_dimensions(self, original_width, original_height):
        """
        Oblicza nowe wymiary obrazu na podstawie ustawień dłuższej i krótszej krawędzi
        
        Args:
            original_width (int): Oryginalna szerokość obrazu
            original_height (int): Oryginalna wysokość obrazu
            
        Returns:
            tuple: (nowa_szerokość, nowa_wysokość) lub None jeśli nie ustawiono wymiarów
        """
        longer_edge = self.longer_edge_input.text()
        shorter_edge = self.shorter_edge_input.text()
        
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
        """Uruchamia proces konwersji plików."""
        if not self.selected_files:
            QMessageBox.warning(self, "Ostrzeżenie", "Nie wybrano plików do konwersji")
            return
        
        # Pobieranie ustawień
        max_size = self.max_size_input.text()
        if max_size and max_size.isdigit():
            max_size = int(max_size)
        else:
            max_size = None
            
        suffix = self.suffix_input.text()
        output_format = self.format_combo.currentText()
        output_dir = self.output_dir_input.text()
        
        number_files_option = self.number_output_files_check.isChecked()
        file_counter = 1 # Zainicjuj licznik dla partii plików
        
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
        
        # Resetuj pasek postępu
        self.progress_bar.setValue(0)
        total_files = len(self.selected_files)
        converted_files = 0
        
        # Wyczyść log przed rozpoczęciem
        self.log_text.clear()
        
        self.log_message("Rozpoczęto proces konwersji...")
        
        for i, image_path in enumerate(self.selected_files):
            try:
                current_number_prefix = None
                if number_files_option:
                    current_number_prefix = f"{file_counter:02d}_" # Format dwucyfrowy z podkreślnikiem

                output_file = self.file_manager.generate_output_filename(
                    image_path, 
                    output_format, 
                    suffix,
                    output_directory=output_dir,
                    number_prefix=current_number_prefix # NOWY ARGUMENT
                )
                self.log_message(f"Konwertowanie: {os.path.basename(image_path)}...")
                QApplication.processEvents()  # Aktualizacja UI
                
                # Otwieramy obraz do sprawdzenia jego wymiarów
                with Image.open(image_path) as img:
                    orig_width, orig_height = img.size
                    
                    # Obliczenie nowych wymiarów
                    new_dimensions = self.calculate_dimensions(orig_width, orig_height)

                strip_metadata_option = self.strip_metadata_check.isChecked()
                webp_lossless_option = False
                if self.format_combo.currentText() == "WebP" and self.webp_lossless_check.isEnabled() and self.webp_lossless_check.isChecked():
                    webp_lossless_option = True
                
                self.converter.convert_heic_to_format(
                    image_path, 
                    output_file,
                    output_format=output_format,
                    max_size_kb=max_size, 
                    new_resolution=new_dimensions,
                    strip_metadata=strip_metadata_option,
                    webp_lossless=webp_lossless_option
                )
                
                self.log_message(f" -> Zapisano jako: {os.path.basename(output_file)}")
                
                # Usuń oryginalny plik, jeśli opcja jest włączona
                if self.delete_originals_check.isChecked():
                    try:
                        os.remove(image_path)
                        self.log_message(f"   Usunięto oryginał: {os.path.basename(image_path)}")
                    except OSError as e:
                        self.log_message(f"   BŁĄD: Nie można usunąć oryginału {os.path.basename(image_path)}: {e}")
                
                # Aktualizacja postępu
                converted_files += 1
                progress_value = int((i + 1) / total_files * 100)
                self.progress_bar.setValue(progress_value)
                QApplication.processEvents()  # Aktualizacja UI

                if number_files_option:
                    file_counter += 1
                
            except Exception as e:
                self.log_message(f"BŁĄD konwersji pliku {os.path.basename(image_path)}: {str(e)}")
        
        self.log_message(f"Konwersja zakończona. Przekonwertowano {converted_files} z {total_files} plików.")
        self.progress_bar.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = ImageConverterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
import os
import sys
import subprocess
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QFrame, 
                            QProgressBar, QTextEdit, QComboBox, QLineEdit, QCheckBox,
                            QGridLayout, QGroupBox, QSplitter, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from config import ConfigManager
from file_manager import FileManager
from image_converter import ImageConverter

class DropArea(QLabel):
    """Obszar do przeciągania i upuszczania plików"""
    filesDropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Upuść pliki obrazów tutaj")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(100)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)
        self.original_style_sheet = self.styleSheet() # Zapisz oryginalny styl

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("background-color: lightblue;") # Podświetlenie
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
        self.setMinimumSize(700, 650)
        
        # Utwórz GUI
        self.create_widgets()
        
        # Załaduj zapisane ustawienia do kontrolek
        self.load_settings_to_ui()
    
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
        
        # Lista wybranych plików - teraz w trybie ikon
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.file_list.setResizeMode(QListWidget.ResizeMode.Adjust) # Ikony będą się układać
        self.file_list.setMovement(QListWidget.Movement.Static)    # Elementy nieprzesuwalne
        self.file_list.setIconSize(Qt.QSize(64, 64)) # Przykładowy rozmiar ikony
        self.file_list.setGridSize(Qt.QSize(80, 80)) # Przykładowy rozmiar komórki siatki
        # Zamiast setMaximumHeight, umieścimy ją w QScrollArea, jeśli potrzebne
        # Na razie zostawiamy bez QScrollArea dla prostoty, zobaczymy jak się zachowuje.
        # Jeśli będzie za dużo plików, QListWidget sam powinien dodać paski przewijania.
        # self.file_list.setMaximumHeight(150) # Zwiększamy trochę wysokość na razie
        file_layout.addWidget(self.file_list)
        
        # Obszar do przeciągania i upuszczania
        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.handle_dropped_files)
        file_layout.addWidget(self.drop_area)
        
        main_layout.addWidget(file_group)
        
        # ==== SEKCJA OPCJI KONWERSJI ====
        options_group = QGroupBox("Opcje konwersji")
        options_layout = QGridLayout()
        options_group.setLayout(options_layout)
        
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
        options_layout.addWidget(self.strip_metadata_check, 7, 0, 1, 3) # Zmieniono span na 3

        main_layout.addWidget(options_group)
        
        # ==== PRZYCISKI AKCJI ====
        action_layout = QHBoxLayout()
        save_settings_btn = QPushButton("Zapisz ustawienia")
        save_settings_btn.clicked.connect(self.save_settings)
        action_layout.addWidget(save_settings_btn)
        
        action_layout.addStretch()
        
        convert_btn = QPushButton("Konwertuj")
        convert_btn.clicked.connect(self.start_conversion)
        action_layout.addWidget(convert_btn)
        
        main_layout.addLayout(action_layout)
        
        # ==== PASEK POSTĘPU ====
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # ==== LOG DZIAŁAŃ ====
        log_group = QGroupBox("Log Działań")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # Ustaw proporcje
        main_layout.setStretch(0, 3)  # File section
        main_layout.setStretch(1, 0)  # Options
        main_layout.setStretch(3, 0)  # Progress
        main_layout.setStretch(4, 2)  # Log

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
        """Przetwarzanie wybranych plików z limitem do 5."""
        # Limit do 5 plików
        files_to_add = files[:5]
        if len(files) > 5:
            QMessageBox.warning(
                self, "Limit plików", 
                "Wybrano więcej niż 5 plików. Tylko pierwsze 5 zostanie dodanych."
            )
        
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
            "webp_lossless": self.webp_lossless_check.isChecked()
        }
        
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
                output_file = self.file_manager.generate_output_filename(
                    image_path, 
                    output_format, 
                    suffix,
                    output_directory=output_dir
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
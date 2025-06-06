import os
import sys
import subprocess
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QFrame, 
                            QProgressBar, QTextEdit, QComboBox, QLineEdit, QCheckBox,
                            QGridLayout, QGroupBox, QSplitter, QMessageBox, QScrollArea, QSizePolicy,
                            QDialog, QDialogButtonBox) # Dodane QDialog i QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl, QSize, QByteArray
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QScreen
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

# ==== KLASA DIALOGU OPCJI ====
class OptionsDialog(QDialog):
    def __init__(self, parent=None, current_options=None, available_formats=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje Konwersji")
        self.setMinimumWidth(450) 
        
        self.available_formats = available_formats if available_formats else \
                                 ["JPEG", "PNG", "BMP", "TIFF", "WebP", "GIF"] # Fallback

        main_dialog_layout = QVBoxLayout(self)

        # Layout dla opcji
        options_layout = QGridLayout()

        # Kontrolki (przeniesione/zreimplementowane z ImageConverterGUI.create_widgets)
        # Format wyjściowy
        options_layout.addWidget(QLabel("Format wyjściowy:"), 0, 0)
        self.format_combo = QComboBox()
        # Zakładamy, że ImageConverter().get_available_formats() jest dostępne,
        # ale lepiej przekazać listę formatów lub instancję converter'a
        self.format_combo.addItems(self.available_formats)
        options_layout.addWidget(self.format_combo, 0, 1)

        # Opcja WebP lossless (powiązana z format_combo)
        self.webp_lossless_check = QCheckBox("WebP bezstratny")
        options_layout.addWidget(self.webp_lossless_check, 0, 2)
        self.format_combo.currentTextChanged.connect(self._update_webp_lossless_state_in_dialog)
        self._update_webp_lossless_state_in_dialog() # Stan początkowy

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
        options_layout.addWidget(self.suffix_input, 4, 1, 1, 2) # Rozciąga się na 2 kolumny
        
        # Katalog wyjściowy (w dialogu może nie być potrzebny przycisk "Otwórz katalog")
        options_layout.addWidget(QLabel("Katalog wyjściowy:"), 5, 0)
        self.output_dir_input = QLineEdit()
        options_layout.addWidget(self.output_dir_input, 5, 1, 1, 2) # Rozciąga się na 2 kolumny
        
        browse_btn = QPushButton("Przeglądaj...")
        browse_btn.clicked.connect(self._select_output_directory_in_dialog) # Podłączono
        options_layout.addWidget(browse_btn, 5, 3)
        
        # Opcja usuwania oryginałów
        self.delete_originals_check = QCheckBox("Usuń oryginalne pliki po udanej konwersji")
        options_layout.addWidget(self.delete_originals_check, 6, 0, 1, 3) # Rozciąga się na 3 kolumny
        
        # Opcja usuwania metadanych
        self.strip_metadata_check = QCheckBox("Usuń metadane (EXIF, ICC, etc.)")
        options_layout.addWidget(self.strip_metadata_check, 7, 0, 1, 3)
        
        # Opcja numerowania plików wynikowych
        self.number_output_files_check = QCheckBox("Numeruj pliki wynikowe (np. 01_nazwa.jpg)")
        options_layout.addWidget(self.number_output_files_check, 8, 0, 1, 3)

        main_dialog_layout.addLayout(options_layout)

        # Przyciski OK / Anuluj
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_dialog_layout.addWidget(button_box)

        if current_options:
            self.set_initial_options(current_options)
        else: # Ustaw stan początkowy dla webp_lossless_check nawet jeśli nie ma current_options
            self._update_webp_lossless_state_in_dialog()


    def _update_webp_lossless_state_in_dialog(self, current_format_text=None):
        """Aktualizuje stan checkboxa WebP lossless na podstawie wybranego formatu w dialogu."""
        if current_format_text is None:
            current_format_text = self.format_combo.currentText()
        
        if current_format_text == "WebP":
            self.webp_lossless_check.setEnabled(True)
        else:
            self.webp_lossless_check.setEnabled(False)
            self.webp_lossless_check.setChecked(False) # Odznacz, jeśli nie WebP

    def _select_output_directory_in_dialog(self):
        """Otwiera dialog wyboru katalogu wyjściowego dla tego dialogu."""
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog wyjściowy", 
            self.output_dir_input.text() # Użyj bieżącej wartości jako startowej
        )
        if directory:
            self.output_dir_input.setText(directory)
            
    def set_initial_options(self, options_dict):
        """Ustawia wartości kontrolek na podstawie przekazanego słownika."""
        self.format_combo.setCurrentText(options_dict.get('output_format', 'JPEG'))
        # Wywołanie _update_webp_lossless_state_in_dialog po ustawieniu formatu
        self._update_webp_lossless_state_in_dialog(self.format_combo.currentText()) 
        
        self.webp_lossless_check.setChecked(options_dict.get('webp_lossless', False))
        self.max_size_input.setText(options_dict.get('max_size', ''))
        self.longer_edge_input.setText(options_dict.get('longer_edge', ''))
        self.shorter_edge_input.setText(options_dict.get('shorter_edge', ''))
        self.suffix_input.setText(options_dict.get('suffix', '_converted'))
        self.output_dir_input.setText(options_dict.get('output_directory', ''))
        self.delete_originals_check.setChecked(options_dict.get('delete_originals', False))
        self.strip_metadata_check.setChecked(options_dict.get('strip_metadata', False))
        self.number_output_files_check.setChecked(options_dict.get('number_output_files', False))

    def get_updated_options(self):
        """Zbiera wartości z kontrolek i zwraca je jako słownik."""
        return {
            'output_format': self.format_combo.currentText(),
            'webp_lossless': self.webp_lossless_check.isChecked(),
            'max_size': self.max_size_input.text(),
            'longer_edge': self.longer_edge_input.text(),
            'shorter_edge': self.shorter_edge_input.text(),
            'suffix': self.suffix_input.text(),
            'output_directory': self.output_dir_input.text(),
            'delete_originals': self.delete_originals_check.isChecked(),
            'strip_metadata': self.strip_metadata_check.isChecked(),
            'number_output_files': self.number_output_files_check.isChecked()
        }

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
        
        # Załaduj zapisane ustawienia do kontrolek - JUŻ NIEPOTRZEBNE W __init__
        # self.load_settings_to_ui() 
        # self.settings są ładowane, a OptionsDialog użyje ich przy otwarciu.
        # Główne okno nie wyświetla już tych opcji bezpośrednio.

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

    def open_options_dialog(self):
        """Otwiera dialog konfiguracji opcji konwersji."""
        # a. Pobierz dostępne formaty z instancji konwertera
        available_formats = self.converter.get_available_formats()

        # b. Utwórz i pokaż dialog, przekazując bieżące ustawienia i dostępne formaty
        # self.settings jest słownikiem, który będzie aktualizowany
        dialog = OptionsDialog(parent=self, current_options=self.settings, available_formats=available_formats)
        
        # c. Jeśli dialog został zaakceptowany (OK), zaktualizuj ustawienia
        if dialog.exec(): # exec() jest blokujące i zwraca QDialog.DialogCode.Accepted lub QDialog.DialogCode.Rejected
            new_settings = dialog.get_updated_options()
            self.settings.update(new_settings) # Aktualizuj główny słownik ustawień
            self.log_message("Zaktualizowano opcje konwersji.")
            # Można rozważyć automatyczne zapisanie ustawień po zmianie w dialogu:
            # self.save_settings() # Jeśli chcemy, aby zmiany były od razu zapisywane do pliku
            # Lub zostawić to użytkownikowi, by kliknął "Zapisz ustawienia" w głównym oknie
        else:
            self.log_message("Anulowano zmiany w opcjach konwersji.")


    def toggle_options_visibility(self, is_checked):
        """Pokazuje lub ukrywa kontener opcji oraz dostosowuje rozmiar okna."""
        
        # a. Zapisz starą wysokość całego QGroupBox "Opcje konwersji"
        old_group_height = self.options_group.height()
        
        # Ustaw widoczność wewnętrznego kontenera
        self.options_container_widget.setVisible(is_checked)
        
        # Poinformuj layout o zmianie geometrii
        self.options_container_widget.updateGeometry() # Aktualizuje sizeHint kontenera
        self.options_group.adjustSize() # Nakazuje QGroupBox dostosować swój rozmiar do zawartości
        if hasattr(self, 'top_widget'): 
             self.top_widget.updateGeometry() # Aktualizuje layout rodzica w splitterze

        # Wymuś przetworzenie zdarzeń, aby widgety miały czas na aktualizację swojej geometrii
        QApplication.processEvents()

        # d. Pobierz nową wysokość całego QGroupBox
        new_group_height = self.options_group.height()
            
        # c. Oblicz delta_height na podstawie zmiany wysokości QGroupBox
        delta_height = new_group_height - old_group_height
        
        # d. Zmień rozmiar głównego okna, jeśli delta jest znacząca
        if abs(delta_height) > 1: # Mniejsza tolerancja, bo adjustSize może być bardziej precyzyjne
            current_window_height = self.height()
            target_window_height = current_window_height + delta_height
            
            # Upewnij się, że nowy rozmiar nie jest mniejszy niż minimalny
            min_h = self.minimumSizeHint().height() 
            # self.minimumHeight() może być bardziej odpowiednie, jeśli zostało jawnie ustawione
            # W naszym przypadku self.setMinimumSize(700, 650) ustawia minimumHeight() na 650
            if self.minimumHeight() > min_h:
                min_h = self.minimumHeight()

            calculated_target_height = max(min_h, target_window_height)

            # Ogranicz wysokość do dostępnej wysokości ekranu
            screen = self.screen() if self.screen() else QApplication.primaryScreen()
            if screen: # Upewnij się, że mamy obiekt screen
                available_screen_height = screen.availableGeometry().height()
                final_window_height = min(calculated_target_height, available_screen_height)
            else: # Fallback, jeśli nie udało się uzyskać ekranu
                final_window_height = calculated_target_height
            
            self.resize(self.width(), final_window_height)
            # self.log_message(f"Zmiana wysokości okna o: {delta_height}, stara_kont: {old_height}, nowa_kont: {new_height}, okno: {final_window_height}")

    # Metoda toggle_options_visibility nie jest już potrzebna, ponieważ QGroupBox opcji został usunięty.
    # def toggle_options_visibility(self, is_checked):
    #     """Pokazuje lub ukrywa kontener opcji oraz dostosowuje rozmiar okna."""
    #     # ... (stara logika) ...

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
        """Załaduj ustawienia z pliku do kontrolek UI (jeśli są jakieś, które nie są w OptionsDialog)."""
        # Ta metoda jest teraz znacznie uproszczona, ponieważ większość kontrolek opcji
        # została przeniesiona do OptionsDialog. 
        # Jeśli w głównym oknie byłyby inne kontrolki, które zależą od self.settings,
        # ich ładowanie odbywałoby się tutaj.
        
        # Przykład: Jeśli self.some_other_main_window_widget zależałoby od ustawienia:
        # self.some_other_main_window_widget.setText(self.settings.get("some_other_setting", "default_value"))
        
        # Usunięto linie odnoszące się do:
        # self.max_size_input, self.longer_edge_input, self.shorter_edge_input, self.suffix_input,
        # self.format_combo, self.output_dir_input, self.delete_originals_check,
        # self.strip_metadata_check, self.webp_lossless_check, self.number_output_files_check,
        # self.options_group, self.options_container_widget,
        # oraz self.update_webp_lossless_check_state() - ponieważ te widgety są teraz w OptionsDialog.
        
        # Jeśli `toggle_options_visibility` i `update_webp_lossless_check_state` są nadal potrzebne
        # jako metody ImageConverterGUI (np. jeśli są wywoływane z innych miejsc),
        # powinny zostać, ale ich logika odnosząca się do nieistniejących widgetów powinna być
        # usunięta lub dostosowana. Zgodnie z poprzednimi krokami, `toggle_options_visibility`
        # zostało usunięte, a `update_webp_lossless_check_state` również powinno być usunięte.
        pass # Obecnie nie ma potrzeby niczego tutaj robić.

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
        file_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        file_group.setFixedHeight(230) # Stała wysokość dla sekcji plików (zwiększona z 180/200)
        
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
        
        # ==== SEKCJA OPCJI KONWERSJI (TERAZ PRZYCISK OTWIERAJĄCY DIALOG) ====
        # Usuwamy stary QGroupBox options_group i jego zawartość
        
        self.options_button = QPushButton("Opcje konwersji...")
        self.options_button.clicked.connect(self.open_options_dialog)
        # Dodajemy przycisk opcji do top_layout, np. przed przyciskami akcji
        # lub w miejscu gdzie był options_group. Zależy od preferencji układu.
        # Na razie dodamy go jako część top_widget, tak jak był options_group.

        # ==== PRZYCISKI AKCJI ====
        action_layout = QHBoxLayout() # Ten layout będzie teraz zawierał tylko "Zapisz ustawienia" i "Konwertuj"
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
        log_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        log_group.setMinimumHeight(150)

        # ==== Konfiguracja Splittera ====
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Górny panel dla file_group, options_group, action_layout, progress_bar
        self.top_widget = QWidget() # Zmieniono na self.top_widget
        self.top_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        top_layout = QVBoxLayout(self.top_widget) # Użyj self.top_widget
        top_layout.addWidget(file_group)
        # top_layout.addWidget(self.options_group) # Usunięto stary options_group
        top_layout.addWidget(self.options_button) # Dodano przycisk opcji
        top_layout.addLayout(action_layout)
        top_layout.addWidget(self.progress_bar)
        # self.top_widget.setLayout(top_layout) # Niepotrzebne, konstruktor QVBoxLayout już to robi

        main_splitter.addWidget(self.top_widget) # Użyj self.top_widget
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

    # Metoda update_webp_lossless_check_state nie jest już potrzebna,
    # ponieważ self.format_combo i self.webp_lossless_check zostały przeniesione do OptionsDialog.
    # def update_webp_lossless_check_state(self, current_format_text=None):
    #     """Aktualizuje stan checkboxa WebP lossless na podstawie wybranego formatu."""
    #     # ... (stara logika) ...
    
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
        # Kopiujemy self.settings, aby uniknąć modyfikacji oryginału, jeśli ConfigManager by to robił
        settings_to_save = self.settings.copy()
        
        # Dodaj/zaktualizuj ustawienia specyficzne dla głównego okna, które nie są w dialogu
        settings_to_save["window_geometry"] = self.saveGeometry().toBase64().data().decode('utf-8')
        # 'options_group_expanded' nie jest już potrzebne, bo QGroupBox opcji został usunięty
        # Jeśli byłyby inne ustawienia UI głównego okna do zapisania, dodaj je tutaj.
        
        self.config_manager.save_settings(settings_to_save)
        self.log_message("Ustawienia zostały zapisane.") # Zmieniono QMessageBox na log_message
        # QMessageBox.information(self, "Informacja", "Ustawienia zostały zapisane") # Można przywrócić, jeśli preferowane
    
    def calculate_dimensions(self, original_width, original_height, longer_edge_str, shorter_edge_str):
        """
        Oblicza nowe wymiary obrazu na podstawie ustawień dłuższej i krótszej krawędzi
        
        Args:
            original_width (int): Oryginalna szerokość obrazu
            original_height (int): Oryginalna wysokość obrazu
            longer_edge_str (str): Wartość dłuższej krawędzi z ustawień (jako string)
            shorter_edge_str (str): Wartość krótszej krawędzi z ustawień (jako string)
            
        Returns:
            tuple: (nowa_szerokość, nowa_wysokość) lub None jeśli nie ustawiono wymiarów
        """
        # longer_edge i shorter_edge są teraz przekazywane jako argumenty
        
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
        longer_edge_val = int(longer_edge_str) if longer_edge_str and longer_edge_str.isdigit() else None
        shorter_edge_val = int(shorter_edge_str) if shorter_edge_str and shorter_edge_str.isdigit() else None
        
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
        
        # Pobieranie ustawień z self.settings
        max_size_str = self.settings.get('max_size', '')
        if max_size_str and max_size_str.isdigit():
            max_size = int(max_size_str)
        else:
            max_size = None
            
        suffix = self.settings.get('suffix', '_converted')
        output_format = self.settings.get('output_format', 'JPEG') # Pobierz z self.settings
        output_dir = self.settings.get('output_directory', '')   # Pobierz z self.settings
        
        number_files_option = self.settings.get('number_output_files', False) # Pobierz z self.settings
        strip_metadata_option = self.settings.get('strip_metadata', False)   # Pobierz z self.settings
        webp_lossless_option = self.settings.get('webp_lossless', False)     # Pobierz z self.settings
        delete_originals_option = self.settings.get('delete_originals', False) # Pobierz z self.settings

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
                    
                    # Obliczenie nowych wymiarów na podstawie wartości z self.settings
                    longer_edge_str = self.settings.get('longer_edge', '')
                    shorter_edge_str = self.settings.get('shorter_edge', '')
                    new_dimensions = self.calculate_dimensions(orig_width, orig_height, longer_edge_str, shorter_edge_str) # Przekaż stringi
                
                # Opcje webp_lossless i strip_metadata są już pobrane z self.settings
                # Nie ma potrzeby ich ponownie sprawdzać z kontrolek
                
                self.converter.convert_heic_to_format(
                    image_path, 
                    output_file,
                    output_format=output_format,
                    max_size_kb=max_size, 
                    new_resolution=new_dimensions,
                    strip_metadata=strip_metadata_option, # Użyj wartości z self.settings
                    webp_lossless=webp_lossless_option   # Użyj wartości z self.settings
                )
                
                self.log_message(f" -> Zapisano jako: {os.path.basename(output_file)}")
                
                # Usuń oryginalny plik, jeśli opcja jest włączona
                if delete_originals_option: # Użyj wartości z self.settings
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
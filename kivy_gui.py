import os
import threading
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.properties import (ObjectProperty, StringProperty, ListProperty, 
                             BooleanProperty, NumericProperty)
from kivy.lang import Builder
from kivy.clock import mainthread
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.factory import Factory

# Załaduj istniejące moduły backendu
from config import ConfigManager
from file_manager import FileManager
from image_converter import ImageConverter
from PIL import Image # Potrzebne do odczytania wymiarów

# Załaduj plik KV (opcjonalnie, ale zalecane)
# Builder.load_file('imageconverter.kv') # Zakładamy, że plik kv istnieje

# Nowa klasa dla elementów listy w RecycleView
class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        self.text = data.get('text', '') 
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected


class ConverterLayout(BoxLayout):
    """Główny layout aplikacji Kivy."""
    log_text_widget = ObjectProperty(None)
    recycle_view_widget = ObjectProperty(None)
    progress_bar_widget = ObjectProperty(None)
    
    # Properties dla powiązania z UI (z pliku kv)
    selected_files_prop = ListProperty([]) # Lista ścieżek
    recycle_view_data = ListProperty([])
    max_size_prop = StringProperty("")
    longer_edge_prop = StringProperty("")
    shorter_edge_prop = StringProperty("")
    suffix_prop = StringProperty("_converted")
    output_format_prop = StringProperty("JPEG")
    output_dir_prop = StringProperty("")
    delete_originals_prop = BooleanProperty(False)
    progress_value_prop = NumericProperty(0)
    
    available_formats_prop = ListProperty([]) # Dla Spinnera

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.file_manager = FileManager()
        self.converter = ImageConverter()
        self.available_formats_prop = self.converter.get_available_formats()
        self.load_settings() # Załaduj ustawienia przy starcie

    @mainthread
    def log_message(self, message):
        if self.log_text_widget:
            self.log_text_widget.text += message + "\n"
            # Automatyczne przewijanie (prosta wersja)
            self.log_text_widget.cursor = (0, len(self.log_text_widget.text))
            self.log_text_widget.scroll_y = 0 

    def load_settings(self):
        settings = self.config_manager.load_settings()
        self.max_size_prop = settings.get("max_size", "")
        self.longer_edge_prop = settings.get("longer_edge", "")
        self.shorter_edge_prop = settings.get("shorter_edge", "")
        self.suffix_prop = settings.get("suffix", "_converted")
        self.output_format_prop = settings.get("output_format", "JPEG")
        self.output_dir_prop = settings.get("output_directory", "")
        self.delete_originals_prop = settings.get("delete_originals", False)
        self.log_message("Ustawienia wczytane.")

    def save_settings(self):
        settings = {
            "max_size": self.max_size_prop,
            "longer_edge": self.longer_edge_prop,
            "shorter_edge": self.shorter_edge_prop,
            "suffix": self.suffix_prop,
            "output_format": self.output_format_prop,
            "output_directory": self.output_dir_prop,
            "delete_originals": self.delete_originals_prop
        }
        self.config_manager.save_settings(settings)
        self.log_message("Ustawienia zapisane.")
        
    def open_file_chooser(self):
        # Prosty FileChooser w Popupie
        popup_layout = BoxLayout(orientation='vertical')
        # Użyj FileChooserListView dla lepszej nawigacji, włącz multiselect
        filechooser = FileChooserListView(filters=["*.heic", "*.HEIC", "*.png", "*.jpg", "*.jpeg"], 
                                         path=os.path.expanduser("~"), multiselect=True)
        popup_layout.add_widget(filechooser)
        
        btn_select = Button(text="Wybierz", size_hint_y=None, height=44)
        popup_layout.add_widget(btn_select)
        
        popup = Popup(title="Wybierz pliki (max 5)", content=popup_layout, size_hint=(0.9, 0.9))
        
        def select_files_action(instance):
            selected = filechooser.selection
            if selected:
                self.process_selected_files(selected)
            popup.dismiss()
            
        btn_select.bind(on_press=select_files_action)
        popup.open()

    def open_dir_chooser(self):
         # Prosty FileChooser w Popupie do wyboru katalogu
        popup_layout = BoxLayout(orientation='vertical')
        # Użyj FileChooserListView ustawionego na wybór katalogów
        filechooser = FileChooserListView(dirselect=True, path=self.output_dir_prop or os.path.expanduser("~"))
        popup_layout.add_widget(filechooser)
        
        btn_select = Button(text="Wybierz Katalog", size_hint_y=None, height=44)
        popup_layout.add_widget(btn_select)
        
        popup = Popup(title="Wybierz katalog wyjściowy", content=popup_layout, size_hint=(0.9, 0.9))
        
        def select_dir_action(instance):
            selected = filechooser.selection
            if selected and os.path.isdir(selected[0]):
                 self.output_dir_prop = selected[0]
                 self.log_message(f"Ustawiono katalog wyjściowy: {self.output_dir_prop}")
            popup.dismiss()
            
        btn_select.bind(on_press=select_dir_action)
        popup.open()

    def process_selected_files(self, files):
        accepted_extensions = ('.heic', '.png', '.jpg', '.jpeg')
        image_files = [f for f in files if os.path.splitext(f.lower())[1] in accepted_extensions and os.path.isfile(f)]
        
        files_to_add = image_files[:5]
        if len(image_files) > 5:
             self.log_message("Ostrzeżenie: Wybrano więcej niż 5 plików. Tylko pierwsze 5 zostanie dodanych.")
        
        self.selected_files_prop = files_to_add
        
        # Aktualizacja danych dla RecycleView
        # Przygotuj dane w formacie oczekiwanym przez RecycleView ({'text': 'nazwa_pliku'})
        self.recycle_view_data = [{'text': os.path.basename(f)} for f in self.selected_files_prop]

        loaded_filenames = [os.path.basename(f) for f in files_to_add]
        if loaded_filenames:
            self.log_message(f"Dodano pliki ({len(loaded_filenames)}): {', '.join(loaded_filenames)}")
        elif image_files: # Jeśli były pliki obrazów, ale nie przeszły walidacji isfile
             self.log_message("Ostrzeżenie: Niektóre wybrane ścieżki nie są plikami.")
        else: # Jeśli nie było żadnych pasujących plików
             self.log_message("Ostrzeżenie: Nie wybrano obsługiwanych plików obrazów (HEIC, PNG, JPG, JPEG)")


    def calculate_dimensions(self, original_width, original_height):
        longer_edge = self.longer_edge_prop
        shorter_edge = self.shorter_edge_prop
        
        if original_width >= original_height:
            original_longer = original_width
            original_shorter = original_height
            is_landscape = True
        else:
            original_longer = original_height
            original_shorter = original_width
            is_landscape = False
        
        if original_shorter == 0:
             return None
             
        aspect_ratio = original_longer / original_shorter
        
        longer_edge_val = int(longer_edge) if longer_edge and longer_edge.isdigit() else None
        shorter_edge_val = int(shorter_edge) if shorter_edge and shorter_edge.isdigit() else None
        
        if longer_edge_val == 0: longer_edge_val = None
        if shorter_edge_val == 0: shorter_edge_val = None
        
        if longer_edge_val and shorter_edge_val:
            new_longer = longer_edge_val
            new_shorter = shorter_edge_val
        elif longer_edge_val:
            new_longer = longer_edge_val
            new_shorter = int(new_longer / aspect_ratio) if aspect_ratio != 0 else original_shorter
        elif shorter_edge_val:
            new_shorter = shorter_edge_val
            new_longer = int(new_shorter * aspect_ratio)
        else:
            return None
            
        if new_longer <= 0 or new_shorter <= 0:
             return None
             
        if is_landscape:
            return (new_longer, new_shorter)
        else:
            return (new_shorter, new_longer)

    def start_conversion_thread(self):
         # Uruchom konwersję w osobnym wątku, aby nie blokować UI
         if not self.selected_files_prop:
            self.log_message("Ostrzeżenie: Nie wybrano plików do konwersji.")
            return
         
         thread = threading.Thread(target=self._conversion_work)
         thread.daemon = True # Wątek zakończy się wraz z głównym programem
         thread.start()

    def _conversion_work(self):
        """Rzeczywista logika konwersji (uruchamiana w wątku)."""
        max_size = self.max_size_prop
        if max_size and max_size.isdigit():
            max_size = int(max_size)
        else:
            max_size = None
            
        suffix = self.suffix_prop
        output_format = self.output_format_prop
        output_dir = self.output_dir_prop
        delete_originals = self.delete_originals_prop
        
        # Sprawdź i utwórz katalog wyjściowy, jeśli podano
        final_output_dir = None
        if output_dir:
            try:
                if self.file_manager.ensure_directory_exists(output_dir):
                    self.log_message(f"Katalog wyjściowy '{output_dir}' istnieje lub został utworzony.")
                    final_output_dir = output_dir
                else:
                    self.log_message(f"OSTRZEŻENIE: Nie można zweryfikować/utworzyć katalogu wyjściowego '{output_dir}'. Pliki będą zapisywane w katalogach źródłowych.")
            except Exception as e:
                self.log_message(f"BŁĄD tworzenia katalogu wyjściowego '{output_dir}': {e}. Pliki będą zapisywane w katalogach źródłowych.")
        
        total_files = len(self.selected_files_prop)
        converted_files = 0
        
        self.log_message("Rozpoczęto proces konwersji...")
        self.update_progress(0) # Reset progress bar

        for i, image_path in enumerate(self.selected_files_prop):
            try:
                output_file = self.file_manager.generate_output_filename(
                    image_path, 
                    output_format, 
                    suffix,
                    output_directory=final_output_dir
                )
                self.log_message(f"Konwertowanie: {os.path.basename(image_path)}...")
                
                new_dimensions = None
                try:
                    # Otwieramy obraz do sprawdzenia jego wymiarów
                    with Image.open(image_path) as img:
                        orig_width, orig_height = img.size
                        new_dimensions = self.calculate_dimensions(orig_width, orig_height)
                except Exception as img_e:
                     self.log_message(f"   BŁĄD odczytu wymiarów {os.path.basename(image_path)}: {img_e}")
                
                self.converter.convert_heic_to_format(
                    image_path, 
                    output_file,
                    output_format=output_format,
                    max_size_kb=max_size, 
                    new_resolution=new_dimensions
                )
                
                self.log_message(f" -> Zapisano jako: {os.path.basename(output_file)}")
                
                # Usuń oryginalny plik, jeśli opcja jest włączona
                if delete_originals:
                    try:
                        os.remove(image_path)
                        self.log_message(f"   Usunięto oryginał: {os.path.basename(image_path)}")
                    except OSError as e:
                        self.log_message(f"   BŁĄD: Nie można usunąć oryginału {os.path.basename(image_path)}: {e}")
                
                converted_files += 1
                
            except Exception as e:
                self.log_message(f"BŁĄD konwersji pliku {os.path.basename(image_path)}: {str(e)}")
            finally:
                # Aktualizacja postępu po każdym pliku (udanym lub nie)
                progress_value = ((i + 1) / total_files) * 100
                self.update_progress(progress_value)

        self.log_message(f"Konwersja zakończona. Przekonwertowano {converted_files} z {total_files} plików.")
        self.update_progress(0) # Reset progress bar po zakończeniu

    @mainthread
    def update_progress(self, value):
        if self.progress_bar_widget:
             self.progress_value_prop = value
             self.progress_bar_widget.value = value


# Kivy App Class
class ImageConverterKivyApp(App):
    def build(self):
        # Zarejestruj widget PRZED załadowaniem pliku KV
        Factory.register('SelectableLabel', cls=SelectableLabel)
        
        # Zamiast ładować plik kv, można budować UI w Pythonie
        # return ConverterLayout() 
        # Jeśli używamy pliku kv, Kivy automatycznie go załaduje
        # jeśli jego nazwa pasuje do nazwy klasy App (bez 'App' i małymi literami)
        # np. imageconverterkivy.kv
        # Lub można załadować ręcznie przez Builder.load_file()
        try:
             # Spróbuj załadować plik KV, jeśli istnieje
             Builder.load_file('imageconverter.kv')
        except Exception as e:
             print(f"Nie można załadować pliku imageconverter.kv: {e}")
             # Można tutaj zbudować podstawowy interfejs w kodzie jako fallback
             pass 
        return ConverterLayout()

# Poniższe widgety Button i Label są potrzebne, jeśli nie używamy pliku KV
# lub jeśli chcemy mieć je dostępne w kodzie Pythona bez odwoływania się przez ids
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout # Do opcji


if __name__ == '__main__':
    # To jest tylko do testowania samego GUI, normalnie uruchamiamy przez kivy_main.py
    ImageConverterKivyApp().run() 
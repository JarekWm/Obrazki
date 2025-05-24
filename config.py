import os
import json

class ConfigManager:
    def __init__(self, config_file="settings.json"):
        self.config_file = config_file
        self.default_settings = {
            "max_size": "",
            "longer_edge": "",
            "shorter_edge": "",
            "suffix": "_converted",
            "output_format": "JPEG",  # Domyślny format wyjściowy
            "output_directory": "",  # Domyślny pusty katalog wyjściowy
            "delete_originals": False  # Domyślnie nie usuwaj oryginałów
        } 
        
    def load_settings(self):
        """
        Wczytuje ustawienia z pliku konfiguracyjnego
        
        Returns:
            dict: Słownik z ustawieniami
        """
        # Sprawdź, czy plik istnieje
        if not os.path.exists(self.config_file):
            # Zapisz domyślne ustawienia, jeśli plik nie istnieje
            self.save_settings(self.default_settings)
            return self.default_settings
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings
        except Exception as e:
            print(f"Błąd podczas wczytywania ustawień: {str(e)}")
            return self.default_settings
    
    def save_settings(self, settings):
        """
        Zapisuje ustawienia do pliku konfiguracyjnego
        
        Args:
            settings (dict): Słownik z ustawieniami do zapisania
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd podczas zapisywania ustawień: {str(e)}")
            
    def get_default_settings(self):
        """
        Zwraca domyślne ustawienia
        
        Returns:
            dict: Słownik z domyślnymi ustawieniami
        """
        return self.default_settings
import os
import io
from PIL import Image
from pillow_heif import register_heif_opener

# Rejestracja obsługi formatów HEIF/HEIC w PILu
register_heif_opener()

class ImageConverter:
    def __init__(self):
        # Dostępne formaty wyjściowe i ich rozszerzenia
        self.formats = {
            "JPEG": "jpg",
            "PNG": "png",
            "BMP": "bmp",
            "TIFF": "tiff",
            "WebP": "webp",
            "GIF": "gif"
        }
        
    def get_available_formats(self):
        """
        Zwraca listę dostępnych formatów wyjściowych
        
        Returns:
            list: Lista dostępnych formatów
        """
        return list(self.formats.keys())
        
    def convert_heic_to_format(self, input_path, output_path, output_format="JPEG", max_size_kb=None, new_resolution=None):
        """
        Konwertuje plik HEIC na wybrany format
        
        Args:
            input_path (str): Ścieżka do pliku HEIC
            output_path (str): Ścieżka do pliku wyjściowego
            output_format (str): Format wyjściowy (JPEG, PNG, BMP, TIFF, WebP, GIF)
            max_size_kb (int, optional): Maksymalny rozmiar pliku wyjściowego w KB
            new_resolution (tuple, optional): Nowa rozdzielczość w formacie (szerokość, wysokość)
            
        Returns:
            str: Ścieżka do utworzonego pliku
        """
        try:
            # Odczyt pliku HEIC przez PIL (dzięki pillow_heif)
            image = Image.open(input_path)
            
            # Konwersja do trybu RGB, jeśli to konieczne
            if image.mode != 'RGB' and output_format != 'PNG':
                image = image.convert('RGB')
            
            # Skalowanie obrazu, jeśli podano nową rozdzielczość
            if new_resolution:
                image = image.resize(new_resolution, Image.Resampling.LANCZOS)
            
            # Opcje zapisu dla różnych formatów
            save_options = {}
            
            # Opcje zależne od formatu
            if output_format == "JPEG":
                save_options["quality"] = 95
                save_options["optimize"] = True
            elif output_format == "PNG":
                save_options["optimize"] = True
                save_options["compress_level"] = 9
            elif output_format == "WebP":
                save_options["quality"] = 90
                save_options["method"] = 6  # najlepsza jakość ale wolniejsza kompresja
            elif output_format == "TIFF":
                save_options["compression"] = "tiff_lzw"
            
            # Jeśli podano max_size_kb i format obsługuje kompresję jakości, dostosuj jakość
            if max_size_kb and output_format in ["JPEG", "WebP"]:
                self._save_with_size_limit(image, output_path, max_size_kb, output_format)
            else:
                # Zapisz z domyślnymi opcjami dla danego formatu
                image.save(output_path, format=output_format, **save_options)
                
            return output_path
        except Exception as e:
            raise Exception(f"Błąd konwersji: {str(e)}")
    
    def _save_with_size_limit(self, image, output_path, max_size_kb, output_format="JPEG"):
        """
        Zapisuje obraz z ograniczeniem rozmiaru
        
        Args:
            image (PIL.Image): Obraz do zapisania
            output_path (str): Ścieżka wyjściowa
            max_size_kb (int): Maksymalny rozmiar w KB
            output_format (str): Format wyjściowy
        """
        max_size_bytes = max_size_kb * 1024
        quality = 95
        min_quality = 20
        
        # Opcje zapisu zależne od formatu
        save_options = {}
        if output_format == "JPEG":
            save_options["optimize"] = True
        elif output_format == "WebP":
            save_options["method"] = 6
        
        # Iteracyjne zmniejszanie jakości aż do osiągnięcia żądanego rozmiaru
        while quality >= min_quality:
            # Zapisz do bufora, aby sprawdzić rozmiar
            temp_buffer = io.BytesIO()
            save_options["quality"] = quality
            image.save(temp_buffer, format=output_format, **save_options)
            current_size = temp_buffer.tell()
            
            if current_size <= max_size_bytes:
                # Zapisz do pliku z odpowiednią jakością
                image.save(output_path, format=output_format, **save_options)
                break
            
            # Zmniejsz jakość
            quality -= 5
            
        # Jeśli nawet z minimalną jakością nie udało się osiągnąć wymaganego rozmiaru
        if quality < min_quality:
            save_options["quality"] = min_quality
            image.save(output_path, format=output_format, **save_options)
            print(f"Uwaga: Nie udało się osiągnąć wymaganego rozmiaru {max_size_kb} KB. Zapisano z minimalną jakością.")
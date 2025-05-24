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
        
    def convert_heic_to_format(self, input_path, output_path, output_format="JPEG", max_size_kb=None, new_resolution=None, strip_metadata: bool = False, webp_lossless: bool = False):
        """
        Konwertuje plik HEIC na wybrany format
        
        Args:
            input_path (str): Ścieżka do pliku HEIC
            output_path (str): Ścieżka do pliku wyjściowego
            output_format (str): Format wyjściowy (JPEG, PNG, BMP, TIFF, WebP, GIF)
            max_size_kb (int, optional): Maksymalny rozmiar pliku wyjściowego w KB
            new_resolution (tuple, optional): Nowa rozdzielczość w formacie (szerokość, wysokość)
            strip_metadata (bool, optional): Czy usunąć metadane z obrazu. Domyślnie False.
            webp_lossless (bool, optional): Czy użyć kompresji bezstratnej dla WebP. Domyślnie False.
            
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
                if strip_metadata:
                    save_options["exif"] = b''
                    save_options["icc_profile"] = None
                else:
                    if 'exif' in image.info:
                        save_options["exif"] = image.info['exif']
                    if 'icc_profile' in image.info:
                        save_options["icc_profile"] = image.info['icc_profile']
            elif output_format == "PNG":
                save_options["optimize"] = True
                save_options["compress_level"] = 9
                if strip_metadata:
                    # Для PNG, Pillow может не иметь прямого способа удалить все метаданные через save_options
                    # image.info может быть очищен перед сохранением, но это не гарантирует удаление всех чанков.
                    # Опция optimize=True помогает уменьшить размер файла, включая некоторые метаданные.
                    # Если требуется более агрессивное удаление, может понадобиться сторонняя библиотека или более сложная обработка.
                    pass  # На данный момент, optimize=True - основная стратегия
            elif output_format == "WebP":
                if webp_lossless:
                    save_options["lossless"] = True
                    save_options["quality"] = 80  # 'Effort' for lossless WebP in Pillow
                    # Method is implicitly 4 for lossless, explicit 'method' can conflict or be ignored.
                    # No 'method' key is set here to use Pillow's default for lossless.
                else:
                    save_options["quality"] = 90
                    save_options["method"] = 6  # For lossy WebP
                    save_options["lossless"] = False
                
                if strip_metadata:
                    save_options["icc_profile"] = None
                    save_options["exif"] = b''
                else:
                    # Preserve metadata if not stripping and present
                    if 'icc_profile' in image.info:
                        save_options["icc_profile"] = image.info['icc_profile']
                    if 'exif' in image.info:
                        save_options["exif"] = image.info['exif']
            elif output_format == "TIFF":
                save_options["compression"] = "tiff_lzw"
                if strip_metadata:
                    # Для TIFF, удаление метаданных может быть сложнее и зависит от конкретных тегов.
                    # Pillow может не предоставлять простой опции для удаления всех метаданных.
                    # Можно попробовать сохранить без определенных тегов, если они известны.
                    pass # На данный момент нет простого способа удалить все метаданные для TIFF
            elif output_format == "BMP":
                # BMP обычно не хранит много метаданных, но на всякий случай
                if strip_metadata:
                    pass # Pillow не предоставляет опций для удаления метаданных для BMP
            elif output_format == "GIF":
                # GIF также обычно не содержит сложных метаданных как EXIF
                if strip_metadata:
                    pass # Pillow не предоставляет опций для удаления метаданных для GIF
            
            # Obsługa max_size_kb i WebP lossless
            if output_format == "WebP" and webp_lossless:
                if max_size_kb is not None:
                    print(f"Ostrzeżenie: Opcja max_size_kb ({max_size_kb} KB) jest ignorowana dla formatu WebP w trybie bezstratnym.")
                # Zapisz bezpośrednio z opcjami bezstratnymi, ignorując _save_with_size_limit
                image.save(output_path, format=output_format, **save_options)
            elif max_size_kb and output_format in ["JPEG", "WebP"]: # WebP lossy or JPEG
                self._save_with_size_limit(image, output_path, max_size_kb, output_format, strip_metadata=strip_metadata, base_save_options=save_options)
            else:
                # Zapisz z domyślnymi opcjami dla danego formatu
                image.save(output_path, format=output_format, **save_options)
                
            return output_path
        except Exception as e:
            raise Exception(f"Błąd konwersji: {str(e)}")
    
    def _save_with_size_limit(self, image, output_path, max_size_kb, output_format="JPEG", strip_metadata: bool = False, base_save_options: dict = None):
        """
        Zapisuje obraz z ograniczeniem rozmiaru
        
        Args:
            image (PIL.Image): Obraz do zapisania
            output_path (str): Ścieżka wyjściowa
            max_size_kb (int): Maksymalny rozmiar w KB
            output_format (str): Format wyjściowy
            strip_metadata (bool): Czy usunąć metadane
            base_save_options (dict): Bazowe opcje zapisu z `convert_heic_to_format`
        """
        # Jeśli WebP jest w trybie bezstratnym, zapisz raz i zakończ, ignorując pętlę jakości.
        if output_format == "WebP" and base_save_options.get("lossless") is True:
            try:
                image.save(output_path, format=output_format, **base_save_options)
                # Sprawdź rozmiar i wydrukuj ostrzeżenie, jeśli przekracza limit (choć nie było próby redukcji)
                if max_size_kb is not None: # max_size_kb jest przekazywane, ale nie używane do iteracji
                    max_size_bytes_check = max_size_kb * 1024
                    if os.path.getsize(output_path) > max_size_bytes_check:
                        print(f"Uwaga: Rozmiar pliku WebP bezstratnego {os.path.getsize(output_path)/(1024):.2f} KB przekracza docelowy limit {max_size_kb} KB. Limit rozmiaru nie jest wymuszany dla WebP bezstratnego.")
            except Exception as e:
                # To jest mało prawdopodobne, jeśli save_options są poprawne, ale na wszelki wypadek
                raise Exception(f"Błąd podczas zapisu WebP bezstratnego w _save_with_size_limit: {str(e)}")
            return

        max_size_bytes = max_size_kb * 1024
        # Dla WebP stratnego, jakość jest już w base_save_options, jeśli była ustawiona.
        # Dla JPEG, jakość jest również w base_save_options.
        quality = base_save_options.get("quality", 95 if output_format == "JPEG" else (90 if output_format == "WebP" and not base_save_options.get("lossless") else None) )
        min_quality = 20 # Minimalna jakość dla JPEG i WebP stratnego
        
        # Użyj kopii base_save_options, aby nie modyfikować oryginału w pętli
        current_save_options = base_save_options.copy() if base_save_options else {}

        # Poniższe warunki dla JPEG i WebP (stratnego) powinny być już obsłużone przez base_save_options
        # przekazane z convert_heic_to_format, w tym strip_metadata.
        # np. current_save_options już będzie miało 'optimize', 'exif', 'icc_profile' dla JPEG
        # lub 'method', 'exif', 'icc_profile' dla WebP stratnego.

        # Iteracyjne zmniejszanie jakości aż do osiągnięcia żądanego rozmiaru
        # (tylko jeśli format wspiera jakość i jakość jest ustawiona - tj. JPEG lub WebP stratny)
        if quality is not None and output_format in ["JPEG", "WebP"] and not current_save_options.get("lossless"):
            while quality >= min_quality:
                current_save_options["quality"] = quality
                temp_buffer = io.BytesIO()
                try:
                    image.save(temp_buffer, format=output_format, **current_save_options)
                    current_size = temp_buffer.tell()
                    
                    if current_size <= max_size_bytes:
                        image.save(output_path, format=output_format, **current_save_options)
                        return # Zapisano pomyślnie
                    
                    quality -= 5
                except Exception as e:
                    # Jeśli wystąpi błąd podczas próby zapisu (np. z powodu nieobsługiwanej kombinacji opcji),
                    # przerwij pętlę i zgłoś problem.
                    raise Exception(f"Błąd podczas iteracyjnego zapisu {output_format} z jakością {quality}: {str(e)}")
            
            # Jeśli pętla zakończyła się, oznacza to, że nie udało się osiągnąć rozmiaru
            # Zapisz z minimalną jakością
            current_save_options["quality"] = min_quality
            try:
                image.save(output_path, format=output_format, **current_save_options)
                print(f"Uwaga: Nie udało się osiągnąć wymaganego rozmiaru {max_size_kb} KB dla {output_format}. Zapisano z minimalną jakością {min_quality}.")
            except Exception as e:
                raise Exception(f"Błąd podczas zapisu {output_format} z minimalną jakością: {str(e)}")
        else:
            # Dla formatów bez kontroli jakości (np. PNG, GIF, BMP) lub WebP lossless (który jest obsługiwany na początku)
            # Zapisz raz z podanymi opcjami (current_save_options pochodzą z base_save_options)
            try:
                image.save(output_path, format=output_format, **current_save_options)
                # Sprawdź rozmiar i wydrukuj ostrzeżenie, jeśli przekracza limit (jeśli max_size_kb było podane)
                if max_size_kb is not None and os.path.getsize(output_path) > max_size_bytes:
                     print(f"Uwaga: Rozmiar pliku {os.path.getsize(output_path)/(1024):.2f} KB przekracza docelowy limit {max_size_kb} KB. Format {output_format} (lub bieżące ustawienia) nie wspiera dostosowania jakości w tej funkcji w celu redukcji rozmiaru, lub jest to WebP bezstratny.")
            except Exception as e:
                raise Exception(f"Błąd podczas zapisu formatu {output_format} bez iteracji jakości: {str(e)}")
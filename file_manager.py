import os

class FileManager:
    def __init__(self):
        # Mapowanie formatów na rozszerzenia plików
        self.format_extensions = {
            "JPEG": "jpg",
            "PNG": "png", 
            "BMP": "bmp", 
            "TIFF": "tiff", 
            "WebP": "webp",
            "GIF": "gif"
        }
    
    def generate_output_filename(self, input_path, output_format="JPEG", suffix="_converted", output_directory=None, number_prefix: str = None):
        """
        Generuje nazwę pliku wyjściowego na podstawie nazwy pliku wejściowego HEIC
        
        Args:
            input_path (str): Ścieżka do pliku wejściowego HEIC
            output_format (str): Format wyjściowy (JPEG, PNG, BMP, TIFF, WebP, GIF)
            suffix (str): Sufiks do dodania przed rozszerzeniem
            output_directory (str, optional): Katalog wyjściowy, jeśli jest inny niż katalog pliku wejściowego
            number_prefix (str, optional): Prefiks numeryczny do dodania na początku nazwy pliku.
            
        Returns:
            str: Ścieżka do pliku wyjściowego
        """
        filename = os.path.basename(input_path)
        
        # Oddziel nazwę pliku od rozszerzenia
        name, ext = os.path.splitext(filename)
        
        # Pobierz właściwe rozszerzenie dla formatu wyjściowego
        extension = self.format_extensions.get(output_format, "jpg")
        
        # Utwórz nową nazwę pliku z sufiksem i rozszerzeniem
        prefix_to_use = number_prefix if number_prefix else ""
        new_filename = f"{prefix_to_use}{name}{suffix}.{extension}"
        
        # Jeśli podano katalog wyjściowy i istnieje, użyj go
        if output_directory and os.path.isdir(output_directory):
            output_path = os.path.join(output_directory, new_filename)
        else:
            # W przeciwnym razie użyj katalogu pliku wejściowego
            directory = os.path.dirname(input_path)
            output_path = os.path.join(directory, new_filename)
        
        return output_path
    
    def get_heic_files_in_directory(self, directory):
        """
        Zwraca listę plików HEIC w podanym katalogu
        
        Args:
            directory (str): Ścieżka do katalogu
            
        Returns:
            list: Lista ścieżek do plików HEIC
        """
        heic_files = []
        
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.heic', '.HEIC')):
                full_path = os.path.join(directory, filename)
                heic_files.append(full_path)
                
        return heic_files
    
    def ensure_directory_exists(self, directory):
        """
        Upewnia się, że podany katalog istnieje, jeśli nie - tworzy go
        
        Args:
            directory (str): Ścieżka do katalogu
            
        Returns:
            bool: True jeśli katalog istnieje lub został utworzony
        """
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                return True
            except Exception as e:
                print(f"Błąd podczas tworzenia katalogu: {str(e)}")
                return False
        return True
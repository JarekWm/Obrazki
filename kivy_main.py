#!/usr/bin/env python3
import sys
import os

# Upewnij się, że Kivy nie przechwytuje argumentów linii poleceń
# os.environ['KIVY_NO_ARGS'] = '1' 

# Opcjonalnie: Ustaw backend graficzny (np. angle_sdl2, sdl2, glew)
# os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

try:
    from kivy_gui import ImageConverterKivyApp
except ImportError as e:
    print("Błąd importu Kivy GUI. Upewnij się, że Kivy jest zainstalowane.")
    print(f"Szczegóły błędu: {e}")
    sys.exit(1)

def main():
    """
    Główna funkcja uruchamiająca aplikację Kivy
    """
    try:
        ImageConverterKivyApp().run()
    except Exception as e:
        # Ogólne przechwytywanie błędów Kivy przy starcie
        print(f"Wystąpił błąd podczas uruchamiania aplikacji Kivy: {e}")
        # Tutaj można dodać logowanie do pliku lub wyświetlić bardziej szczegółowy błąd
        sys.exit(1)

if __name__ == "__main__":
    main() 
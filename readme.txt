# Konwerter Obrazów - Instrukcja

## Opis
Aplikacja służy do konwersji plików obrazów z formatów HEIC, PNG, JPG/JPEG do innych formatów graficznych. Program posiada przyjazny interfejs graficzny umożliwiający wybór plików, konfigurację opcji konwersji i zarządzanie wynikowymi plikami.

## Wymagania
Aplikacja posiada trzy wersje interfejsu: Tkinter (standardowa), PyQt6 (nowoczesna) oraz Kivy (wieloplatformowa).

### Zależności podstawowe (wymagane dla wszystkich wersji):
```
pip install pillow-heif
pip install pillow
```

### Dla wersji Tkinter (domyślna):
```
pip install tkinterdnd2
```

### Dla wersji PyQt6:
```
pip install PyQt6
```

### Dla wersji Kivy:
```
pip install kivy
# Na niektórych systemach mogą być potrzebne dodatkowe zależności systemowe dla Kivy.
# Zobacz: https://kivy.org/doc/stable/gettingstarted/installation.html
```

## Uruchomienie

### Wersja Tkinter:
```
python main.py
# lub
python main_gui.py
```

### Wersja PyQt6:
```
python qt_main.py
```

### Wersja Kivy:
```
python kivy_main.py
```

## Funkcjonalność
- Obsługa formatów wejściowych: HEIC, PNG, JPG/JPEG
- Konwersja do różnych formatów wyjściowych (JPEG, PNG, BMP, TIFF, WebP, GIF)
- Możliwość określenia maksymalnego rozmiaru pliku wynikowego (dla JPEG, WebP)
- Kontrola rozdzielczości poprzez ustawienie dłuższej i/lub krótszej krawędzi
- Wybór katalogu zapisu plików wynikowych
- Opcjonalne usuwanie plików oryginalnych po konwersji
- Możliwość zapisywania ustawień (plik `settings.json`)
- Dziennik działań (log) z informacjami o procesie konwersji
- Wybór plików przez okno dialogowe lub przeciągnij i upuść (w wersjach Tkinter i PyQt6)
- Wybór plików przez okno dialogowe (w wersji Kivy)

## Ograniczenia
- Jednorazowo można wybrać maksymalnie 5 plików do konwersji
- Opcja maksymalnego rozmiaru działa tylko dla formatów JPEG i WebP
- Wersja Kivy GUI nie implementuje obecnie funkcji przeciągnij i upuść.
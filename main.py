import tkinter as tk
from tkinterdnd2 import TkinterDnD
from main_gui import ImageConverterGUI

def main():
    """
    Główna funkcja uruchamiająca aplikację
    """
    # Utwórz główne okno aplikacji z obsługą drag and drop
    root = TkinterDnD.Tk()
    
    # Ustaw tytuł
    root.title("Konwerter Obrazów")
    
    # Inicjalizuj interfejs użytkownika
    app = ImageConverterGUI(root)
    
    # Uruchom główną pętlę aplikacji
    root.mainloop()

if __name__ == "__main__":
    main()
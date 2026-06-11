import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from main_window import MainWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def main():
    """
    Point d'entrée principal de l'application Antigravity PDF Editor Pro.
    Initialise l'application PyQt6 et affiche la fenêtre principale.
    """
    app = QApplication(sys.argv)
    
    # Définir l'icône globale de l'application
    icon_path = resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Définition du style global de l'application si nécessaire
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

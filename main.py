import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtGui import QScreen, QIcon  
from lista import create_list_tab
import os
import json
from encriptador import create_encryption_tab
from media import create_media_player_tab  # Importando a função para criar a aba Media Player

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.save_directory = None

        # Configurações da janela principal
        self.setWindowTitle("Dahaka Encryptor")
        self.setGeometry(100, 100, 800, 650)

        # Definir o ícone da aplicação (certifique-se de que o arquivo 'icone.ico' está no mesmo diretório do script)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icone.ico')))

        # Centralizar a janela ao abrir
        self.center()

        # Adicionando um estilo escuro para a aplicação
        self.dark_stylesheet = """
                    QWidget {
                        background-color: #121212;
                        color: #e0e0e0;
                        font-family: 'Segoe UI', Tahoma, Geneva, sans-serif;
                        font-size: 14px;
                    }
                    QTabWidget::pane {
                        background-color: #1f1f1f;
                        border: 1px solid #2c2c2c;
                        border-radius: 8px;
                        padding: 5px;
                    }
                    QTabBar::tab {
                        background-color: #2c2c2c;
                        color: #e0e0e0;
                        padding: 10px;
                        margin: 2px;
                        border-top-left-radius: 10px;
                        border-top-right-radius: 10px;
                        border: 1px solid #2c2c2c;
                    }
                    QTabBar::tab:selected {
                        background-color: #3a3a3a;
                        color: #ffffff;
                        border-color: #3a3a3a;
                        font-weight: bold;
                    }
                    QTabBar::tab:hover {
                        background-color: #333333;
                        color: #ffffff;
                    }
                    QPushButton {
                        background-color: #2e2e2e;
                        color: #e0e0e0;
                        border: 1px solid #3a3a3a;
                        border-radius: 6px;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #383838;
                        color: #ffffff;
                        border: 1px solid #4a4a4a;
                    }
                    QPushButton:pressed {
                        background-color: #1f1f1f;
                        color: #e0e0e0;
                        border: 1px solid #3a3a3a;
                    }
                    QLabel {
                        color: #e0e0e0;
                        font-weight: normal;
                    }
                    QScrollArea {
                        border: none;
                        background-color: #1f1f1f;
                    }
                    QTextEdit {
                        background-color: #1f1f1f;
                        color: #e0e0e0;
                        border: 1px solid #2c2c2c;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QListWidget {
                        background-color: #1f1f1f;
                        color: #e0e0e0;
                        border: 1px solid #2c2c2c;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QListWidget::item {
                        padding: 10px;
                    }
                    QListWidget::item:selected {
                        background-color: #3a3a3a;
                        color: #ffffff;
                    }
                """


        # Aplicando o tema escuro
        self.setStyleSheet(self.dark_stylesheet)

        # Criando o TabWidget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Criando as abas
        create_list_tab(self)           # Função modularizada para a aba "Lista"
        create_encryption_tab(self)     # Função modularizada para a aba "Encriptador"
        create_media_player_tab(self)   # Criando a aba Media Player

        # Variáveis para armazenar informações da mídia selecionada
        self.selected_media_file = None
        self.selected_media_name = None

    def center(self):
        # Obter a tela principal
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Obter a geometria da janela
        window_geometry = self.frameGeometry()

        # Definir o centro da tela
        screen_center = screen_geometry.center()

        # Mover o centro da janela para o centro da tela
        window_geometry.moveCenter(screen_center)

        # Mover a janela para a nova posição centralizada
        self.move(window_geometry.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

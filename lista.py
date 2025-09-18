import os
from PyQt6.QtGui import QColor
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QMessageBox, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt
from encriptador import derive_key_from_password  # Importando a função de derivação de chave

def create_list_tab(main_window):
    # Criando a aba da Lista
    list_tab = QWidget()
    layout = QVBoxLayout()

    # Botão para selecionar diretório
    select_dir_button = QPushButton("Selecionar Diretório")
    select_dir_button.clicked.connect(lambda: open_directory_dialog(main_window))
    layout.addWidget(select_dir_button)

    # Lista para exibir os arquivos descriptografados
    main_window.file_list_widget = QListWidget()
    main_window.file_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Permitir seleção por arrasto
    main_window.file_list_widget.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)  # Garantir que selecione uma linha por vez
    layout.addWidget(main_window.file_list_widget)

    # Label para avisos
    main_window.warning_label = QLabel("")
    main_window.warning_label.setStyleSheet("color: red;")
    layout.addWidget(main_window.warning_label)

    # Botão para abrir o arquivo no Media Player
    open_media_button = QPushButton("Abrir Mídia")
    open_media_button.clicked.connect(lambda: open_media_in_player(main_window))
    layout.addWidget(open_media_button)

    # Botão para descriptografar arquivos
    decrypt_button = QPushButton("Descriptografar Arquivos Selecionados")
    decrypt_button.clicked.connect(lambda: decrypt_selected_files(main_window))
    layout.addWidget(decrypt_button)

    list_tab.setLayout(layout)
    main_window.tabs.addTab(list_tab, "Lista")

    # Dicionário para armazenar caminhos completos dos arquivos
    main_window.file_paths = {}


def open_directory_dialog(main_window):
    directory = QFileDialog.getExistingDirectory(main_window, "Selecionar Diretório")
    if directory:
        list_files_in_directory(main_window, directory)

def list_files_in_directory(main_window, directory):
    main_window.file_list_widget.clear()  # Limpa a lista antes de adicionar novos arquivos
    main_window.file_paths.clear()  # Limpa o dicionário de caminhos
    found_encrypted_files = False  # Variável para verificar se encontrou arquivos criptografados
    
    try:
        # Pega a chave predefinida e a senha de criptografia inserida
        base_key = main_window.key_input.text()
        password = main_window.password_input.text()

        # Derivar a chave de criptografia usando a senha do usuário
        if not password:
            QMessageBox.warning(main_window, "Erro", "Por favor, insira uma senha de criptografia.")
            return

        derived_key = derive_key_from_password(password, base_key)
        cipher = Fernet(derived_key)

        # Função recursiva para percorrer o diretório e listar arquivos
        def scan_directory(current_directory, indent_level=0):
            nonlocal found_encrypted_files

            # Adicionar diretório com fundo diferente e não selecionável
            dir_item = QListWidgetItem(" " * indent_level + os.path.basename(current_directory) + "/")
            dir_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Faz com que o diretório não seja selecionável
            dir_item.setBackground(QColor("#452C19"))   # Define uma cor de fundo diferente para diretórios
            main_window.file_list_widget.addItem(dir_item)

            # Listar os subdiretórios e arquivos sem fazer nova chamada para `os.walk()`
            subdirs = []
            files = []

            # Percorre o diretório atual
            for item in os.listdir(current_directory):
                item_path = os.path.join(current_directory, item)
                if os.path.isdir(item_path):
                    subdirs.append(item_path)  # Coleta subdiretórios
                else:
                    files.append(item_path)  # Coleta arquivos

            # Processar subdiretórios
            for subdir in subdirs:
                scan_directory(subdir, indent_level + 4)

            # Processar arquivos
            for file_path in files:
                file_name = os.path.basename(file_path)
                if '.' not in file_name:  # Ignora arquivos que já possuem extensão
                    try:
                        # Descriptografar o nome do arquivo
                        decrypted_name = cipher.decrypt(file_name.encode()).decode()

                        # Adicionar o nome descriptografado à lista com indentação e fundo padrão
                        file_item = QListWidgetItem(" " * (indent_level + 4) + decrypted_name)
                        file_item.setBackground(QColor("#1C2A36"))  # Define fundo diferente para arquivos
                        main_window.file_list_widget.addItem(file_item)

                        # Armazenar o caminho completo no dicionário com o nome descriptografado como chave
                        main_window.file_paths[decrypted_name] = file_path
                        found_encrypted_files = True  # Marca que encontrou um arquivo criptografado

                    except Exception:
                        # Ignora o erro ao descriptografar e continua com o próximo arquivo
                        pass

        # Iniciar a varredura a partir do diretório selecionado
        scan_directory(directory)

        if not found_encrypted_files:
            main_window.warning_label.setText("Nenhum arquivo criptografado encontrado.")
            main_window.warning_label.setStyleSheet("color: orange;")

    except Exception as e:
        main_window.file_list_widget.addItem(f"Erro ao listar arquivos: {str(e)}")


def open_media_in_player(main_window):
    selected_items = main_window.file_list_widget.selectedItems()

    # Verificar se mais de um arquivo foi selecionado
    if len(selected_items) != 1:
        main_window.warning_label.setText("Por favor, selecione apenas um arquivo para abrir.")
        return

    main_window.warning_label.setText("")  # Limpar aviso anterior, se houver

    # Obtém o nome descriptografado selecionado
    decrypted_name = selected_items[0].text().strip()

    # Recupera o caminho completo do arquivo a partir do dicionário
    file_path = main_window.file_paths.get(decrypted_name, None)
    if not file_path:
        QMessageBox.warning(main_window, "Erro", "Caminho do arquivo não encontrado.")
        return

    # Definindo as informações para o Media Player
    main_window.selected_media_file = file_path
    main_window.selected_media_name = decrypted_name

    # Mudar para a aba Media Player
    main_window.tabs.setCurrentIndex(main_window.tabs.indexOf(main_window.media_player_tab))

    # Atualizar a aba Media Player com as informações do arquivo
    main_window.update_media_player()


def decrypt_selected_files(main_window):
    selected_items = main_window.file_list_widget.selectedItems()

    if not selected_items:
        QMessageBox.warning(main_window, "Aviso", "Nenhum arquivo selecionado para descriptografar.")
        return

    # Selecionar diretório de salvamento para os arquivos descriptografados
    output_directory = QFileDialog.getExistingDirectory(main_window, "Selecionar Diretório de Salvamento")
    if not output_directory:
        QMessageBox.warning(main_window, "Erro", "Nenhum diretório de salvamento selecionado.")
        return

    # Pega a chave predefinida e a senha de criptografia inserida
    base_key = main_window.key_input.text()
    password = main_window.password_input.text()

    # Derivar a chave de criptografia usando a senha do usuário
    if not password:
        QMessageBox.warning(main_window, "Erro", "Por favor, insira uma senha de criptografia.")
        return

    derived_key = derive_key_from_password(password, base_key)
    cipher = Fernet(derived_key)

    for item in selected_items:
        decrypted_name = item.text().strip()
        file_path = main_window.file_paths.get(decrypted_name)

        if file_path:
            try:
                # Ler o conteúdo criptografado do arquivo
                with open(file_path, 'rb') as encrypted_file:
                    encrypted_data = encrypted_file.read()

                # Descriptografar o conteúdo
                decrypted_data = cipher.decrypt(encrypted_data)

                # Restaurar a extensão original do arquivo a partir do nome descriptografado
                file_base, file_extension = os.path.splitext(decrypted_name)

                # Caminho completo para salvar o arquivo descriptografado
                output_file_path = os.path.join(output_directory, f"{file_base}{file_extension}")

                # Escrever o conteúdo descriptografado no novo arquivo
                with open(output_file_path, 'wb') as decrypted_file:
                    decrypted_file.write(decrypted_data)

                # Exibir mensagem de sucesso em verde e curta
                main_window.warning_label.setText("Descriptografado com sucesso.")
                main_window.warning_label.setStyleSheet("color: green;")
            except Exception as e:
                QMessageBox.critical(main_window, "Erro", f"Erro ao descriptografar o arquivo {decrypted_name}: {str(e)}")

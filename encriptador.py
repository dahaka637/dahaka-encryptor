import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import random
from base64 import urlsafe_b64encode
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QListWidget, QLabel, QFileDialog, QMenu, QHBoxLayout

def create_encryption_tab(main_window):
    # Criando a aba do Encriptador
    encryption_tab = QWidget()
    layout = QVBoxLayout()

    main_window.selected_items = []

    # Layout horizontal para os botões e o label "Chave de Criptografia"
    key_layout = QHBoxLayout()

    # Label para "Chave de Criptografia"
    label_key = QLabel("Chave de Criptografia:")
    key_layout.addWidget(label_key)

    # Botão de gerar chave
    generate_key_button = QPushButton("Gerar Chave")
    generate_key_button.clicked.connect(lambda: generate_key(main_window))
    key_layout.addWidget(generate_key_button)

    # Botão de salvar chave
    save_key_button = QPushButton("Salvar Chave")
    save_key_button.clicked.connect(lambda: save_key(main_window))
    key_layout.addWidget(save_key_button)

    # Adicionando o layout dos botões e do label ao layout principal
    layout.addLayout(key_layout)

    # Entrada de chave de criptografia (campo de texto vazio inicialmente)
    main_window.key_input = QLineEdit()  # Campo de chave vazio
    main_window.key_input.setPlaceholderText("Chave de Criptografia")
    layout.addWidget(main_window.key_input)

    # Entrada de senha de criptografia (usuário)
    main_window.password_input = QLineEdit()
    main_window.password_input.setPlaceholderText("Senha de Criptografia")
    main_window.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Ofuscar a entrada
    layout.addWidget(QLabel("Senha de Criptografia:"))
    layout.addWidget(main_window.password_input)

    # Botão para selecionar arquivos
    select_file_button = QPushButton("Selecionar Arquivos")
    select_file_button.clicked.connect(lambda: select_files(main_window))
    layout.addWidget(select_file_button)

    # Botão para selecionar um diretório completo
    select_directory_button = QPushButton("Selecionar Diretório Completo")
    select_directory_button.clicked.connect(lambda: select_directory(main_window))
    layout.addWidget(select_directory_button)

    # Lista para mostrar arquivos ou diretórios selecionados
    main_window.file_info_label = QListWidget()
    layout.addWidget(main_window.file_info_label)

    # Botão para selecionar o diretório de salvamento
    select_save_directory_button = QPushButton("Selecionar Diretório de Salvamento")
    select_save_directory_button.clicked.connect(lambda: select_save_directory(main_window))
    layout.addWidget(select_save_directory_button)

    # Botão para criptografar
    encrypt_button = QPushButton("Criptografar Arquivos/Diretório")
    encrypt_button.clicked.connect(lambda: encrypt_files_or_directory(main_window))
    layout.addWidget(encrypt_button)

    # Feedback do processo
    main_window.feedback_label = QLabel("")
    layout.addWidget(main_window.feedback_label)

    encryption_tab.setLayout(layout)
    main_window.tabs.addTab(encryption_tab, "Encriptador")

    # Associando funções ao main_window
    main_window.encrypt_file = lambda file_path, cipher, root_directory, base_encrypted_directory: \
        encrypt_file(main_window, file_path, cipher, root_directory, base_encrypted_directory)

    main_window.encrypt_directory = lambda directory, cipher, base_encrypted_directory: \
        encrypt_directory(main_window, directory, cipher, base_encrypted_directory)  # <-- Correção aqui


    # Habilitar menu contextual para remover itens
    main_window.file_info_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.file_info_label.customContextMenuRequested.connect(lambda pos: show_context_menu(main_window, pos))

    # Carregar a chave do arquivo encryption_key.json, se existir
    load_key_from_json(main_window)


# Função para selecionar arquivos
def select_files(main_window):
    files, _ = QFileDialog.getOpenFileNames(main_window, "Selecionar Arquivos", "", "Todos os Arquivos (*)")

    # Adicionar arquivos à lista de itens selecionados
    for file in files:
        main_window.file_info_label.addItem(f"{file}")

    # Atualizar a lista de itens selecionados no main_window
    main_window.selected_items.extend(files)

# Função para selecionar um diretório completo
def select_directory(main_window):
    directory = QFileDialog.getExistingDirectory(main_window, "Selecionar Diretório")
    if directory:
        # Adicionar o diretório à lista de itens selecionados ao invés de listar arquivos individualmente
        main_window.file_info_label.addItem(f"{directory}")
        main_window.selected_items.append(directory)

    # Exibe uma mensagem caso um diretório não seja selecionado
    else:
        print("Nenhum diretório foi selecionado.")



def show_context_menu(main_window, pos):
    # Verificar se algum item foi selecionado
    selected_item = main_window.file_info_label.itemAt(pos)
    if selected_item:
        context_menu = QMenu(main_window.file_info_label)
        remove_action = context_menu.addAction("Remover")
        
        # Ação para remover o item selecionado
        action = context_menu.exec(main_window.file_info_label.mapToGlobal(pos))
        
        if action == remove_action:
            row = main_window.file_info_label.row(selected_item)
            main_window.file_info_label.takeItem(row)
            if len(main_window.selected_items) > row:
                main_window.selected_items.pop(row)


def derive_key_from_password(password, base_key):
    """
    Derivar a chave de criptografia usando PBKDF2 (combinando chave pré-definida + senha do usuário)
    """
    salt = base_key.encode()  # Usar a chave base como sal
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    derived_key = kdf.derive(password.encode())
    return urlsafe_b64encode(derived_key)  # Retorna a chave em formato base64 seguro para URLs


def save_key(main_window):
    """
    Salva a chave de criptografia em um arquivo JSON na mesma pasta onde o script está localizado.
    """
    key = main_window.key_input.text()

    # Caminho do arquivo JSON (mesmo diretório do script)
    script_directory = os.path.dirname(os.path.abspath(__file__))  # Diretório do script atual
    json_file_path = os.path.join(script_directory, "encryption_key.json")  # Caminho completo do arquivo JSON

    # Dicionário com a chave de criptografia
    key_data = {"encryption_key": key}

    try:
        # Salvar a chave no arquivo JSON
        with open(json_file_path, 'w') as json_file:
            json.dump(key_data, json_file, indent=4)

        # Mensagem de sucesso
        main_window.feedback_label.setText("Chave salva com sucesso!")
        main_window.feedback_label.setStyleSheet("color: green;")

    except Exception as e:
        # Mensagem de erro
        main_window.feedback_label.setText(f"Erro ao salvar a chave: {str(e)}")
        main_window.feedback_label.setStyleSheet("color: red;")

def load_key_from_json(main_window):
    """
    Verifica se o arquivo encryption_key.json existe e, se for válido, carrega a chave de criptografia.
    """
    try:
        # Caminho do arquivo JSON no diretório do script
        script_directory = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_directory, "encryption_key.json")

        # Verifica se o arquivo existe
        if os.path.exists(json_file_path):
            # Ler o conteúdo do arquivo JSON
            with open(json_file_path, 'r') as json_file:
                key_data = json.load(json_file)

            # Verifica se o JSON contém a chave de criptografia
            if "encryption_key" in key_data:
                main_window.key_input.setText(key_data["encryption_key"])
                main_window.feedback_label.setText("Chave carregada com sucesso!")
                main_window.feedback_label.setStyleSheet("color: green;")
            else:
                main_window.feedback_label.setText("Arquivo de chave inválido.")
                main_window.feedback_label.setStyleSheet("color: red;")
        else:
            main_window.feedback_label.setText("Nenhum arquivo de chave encontrado.")
            main_window.feedback_label.setStyleSheet("color: orange;")  # Mensagem neutra caso o arquivo não exista
    except Exception as e:
        # Caso ocorra algum erro durante a leitura do arquivo
        main_window.feedback_label.setText(f"Erro ao carregar chave: {str(e)}")
        main_window.feedback_label.setStyleSheet("color: red;")


def generate_key(main_window):
    """
    Gera uma nova chave de criptografia Fernet e insere no campo de chave
    """
    new_key = Fernet.generate_key().decode()  # Gera uma nova chave Fernet
    main_window.key_input.setText(new_key)

def select_save_directory(main_window):
    main_window.save_directory = QFileDialog.getExistingDirectory(main_window, "Selecionar Diretório de Salvamento")
    if main_window.save_directory:
        main_window.feedback_label.setText(f"Diretório de salvamento: {main_window.save_directory}")
        main_window.feedback_label.setStyleSheet("color: green;")
    else:
        main_window.feedback_label.setText("Por favor, selecione um diretório de salvamento.")
        main_window.feedback_label.setStyleSheet("color: red;")


########## CRIPTOGRAFIA

# Função atualizada para criptografar arquivos ou diretórios
def encrypt_files_or_directory(main_window):
    if not main_window.selected_items:
        main_window.feedback_label.setText("Selecione arquivos ou diretórios primeiro.")
        main_window.feedback_label.setStyleSheet("color: red;")
        return

    # Exibir a organização de diretórios e arquivos
    print("\nDepurando estrutura do(s) diretório(s) selecionado(s):")
    for item in main_window.selected_items:
        if os.path.isdir(item):
            print(f"\nAnalisando diretório selecionado: {os.path.basename(item)}")
            for root, dirs, files in os.walk(item):
                print(f"  Diretório: {root}")
                for dir_name in dirs:
                    print(f"    Subdiretório: {dir_name}")
                for file_name in files:
                    print(f"    Arquivo: {file_name}")
        elif os.path.isfile(item):
            print(f"Arquivo individual selecionado: {os.path.basename(item)}")

    # Derivar a chave de criptografia usando a senha do usuário
    base_key = main_window.key_input.text()
    password = main_window.password_input.text()

    if not password:
        main_window.feedback_label.setText("Por favor, insira uma senha de criptografia.")
        main_window.feedback_label.setStyleSheet("color: red;")
        return

    derived_key = derive_key_from_password(password, base_key)
    cipher = Fernet(derived_key)

    # Se o usuário não selecionar um diretório de salvamento, usar o mesmo diretório de origem
    if not main_window.save_directory:
        main_window.save_directory = os.path.dirname(main_window.selected_items[0])

    # Gerar 6 números aleatórios para o nome da pasta de saída
    random_suffix = random.randint(100000, 999999)
    base_encrypted_directory = os.path.join(main_window.save_directory, f"encripted_files_{random_suffix}")
    if not os.path.exists(base_encrypted_directory):
        os.makedirs(base_encrypted_directory)

    print(f"\nBase encrypted directory criado: {base_encrypted_directory}")

    # Percorrer os itens selecionados e criptografá-los
    for item in main_window.selected_items:
        if os.path.isfile(item):
            # Para arquivos, apenas criptografa e salva
            main_window.encrypt_file(item, cipher, os.path.dirname(item), base_encrypted_directory)
        elif os.path.isdir(item):
            # Para diretórios, recria a estrutura e criptografa os arquivos
            root_folder_name = os.path.basename(item)  # Nome da pasta raiz (ex: "pasta_01")
            root_encrypted_path = os.path.join(base_encrypted_directory, root_folder_name)

            if not os.path.exists(root_encrypted_path):
                os.makedirs(root_encrypted_path)

            print(f"Diretório raiz do diretório criptografado: {root_encrypted_path}")

            # Recriar a estrutura de pastas e criptografar os arquivos
            create_directory_structure(item, root_encrypted_path)
            main_window.encrypt_directory(item, cipher, root_encrypted_path)

    main_window.feedback_label.setText("Arquivos/Diretórios criptografados com sucesso!")
    main_window.feedback_label.setStyleSheet("color: green;")

def create_directory_structure(source_directory, destination_directory):
    """
    Recria a estrutura de pastas do diretório de origem no diretório de destino.
    """
    for root, dirs, files in os.walk(source_directory):
        relative_path = os.path.relpath(root, start=source_directory)
        target_dir = os.path.join(destination_directory, relative_path)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Criando diretório: {target_dir}")
        else:
            print(f"Diretório já existe: {target_dir}")

def encrypt_directory(main_window, directory, cipher, base_encrypted_directory):
    """
    Criptografa os arquivos em um diretório, preservando a estrutura de pastas.
    """
    for root, dirs, files in os.walk(directory):
        relative_path = os.path.relpath(root, start=directory)
        target_dir = os.path.join(base_encrypted_directory, relative_path)

        for file in files:
            file_path = os.path.join(root, file)
            print(f"Criptografando arquivo: {file[:5]}... -> para: {target_dir}")
            main_window.encrypt_file(file_path, cipher, directory, base_encrypted_directory)

def encrypt_file(main_window, file_path, cipher, root_directory, base_encrypted_directory):
    """
    Criptografa um arquivo e o salva no diretório encriptado, preservando a estrutura.
    """
    try:
        # Ler o conteúdo do arquivo
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Criptografar o conteúdo
        encrypted_data = cipher.encrypt(file_data)

        # Separar o nome base e a extensão
        file_base, file_extension = os.path.splitext(os.path.basename(file_path))

        # Concatenar o nome base com a extensão antes de criptografar o nome
        name_with_extension = f"{file_base}{file_extension}"
        encrypted_file_name = cipher.encrypt(name_with_extension.encode()).decode()

        # Gerar o caminho relativo do arquivo em relação ao diretório raiz selecionado
        relative_path = os.path.relpath(file_path, start=root_directory)

        # Caminho final de salvamento dentro de `encripted_files_<6_números_aleatórios>`
        save_path = os.path.join(base_encrypted_directory, relative_path)

        # Criar diretórios necessários para manter a estrutura original
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Salvar o arquivo criptografado
        with open(os.path.join(save_dir, encrypted_file_name), 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

        print(f"Arquivo criptografado salvo: {encrypted_file_name[:10]}... em {save_dir}")

    except Exception as e:
        main_window.feedback_label.setText(f"Erro ao criptografar: {str(e)}")
        main_window.feedback_label.setStyleSheet("color: red;")

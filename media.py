from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QSizePolicy, QTextEdit, QSlider, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import vlc
from cryptography.fernet import Fernet
import tempfile
import os
import fitz  
from encriptador import derive_key_from_password  # Importando a função de derivação da chave


def create_media_player_tab(main_window):
    # Criando a aba do Media Player
    media_player_tab = QWidget()
    layout = QVBoxLayout()

    # Label para mostrar o nome do arquivo selecionado
    main_window.media_file_label = QLabel("Nenhum arquivo selecionado")
    main_window.media_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(main_window.media_file_label)

    # Criando QScrollArea para imagens e PDFs
    main_window.scroll_area = QScrollArea()
    main_window.scroll_area.setWidgetResizable(True)

    # Label para exibir imagens
    main_window.image_label = QLabel()
    main_window.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_window.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    main_window.image_label.setScaledContents(True)

    # Definir o image_label como widget dentro da QScrollArea
    main_window.scroll_area.setWidget(main_window.image_label)

    # Adicionar a área de rolagem ao layout
    layout.addWidget(main_window.scroll_area)

    # Widget para exibir vídeos (QVideoWidget do VLC)
    main_window.video_widget = QLabel("")
    main_window.video_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_window.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    layout.addWidget(main_window.video_widget)

    # Caixa de texto para exibir e editar conteúdo de outros arquivos
    main_window.text_edit = QTextEdit()
    main_window.text_edit.setVisible(False)
    layout.addWidget(main_window.text_edit)

    # Controles dinâmicos de acordo com o tipo de arquivo
    main_window.controls_layout = QHBoxLayout()
    layout.addLayout(main_window.controls_layout)

    # Adicionar botões de zoom (inicialmente escondidos)
    main_window.zoom_layout = QHBoxLayout()  # Salvar o layout de zoom no main_window
    main_window.zoom_in_button = QPushButton("Zoom In")
    main_window.zoom_out_button = QPushButton("Zoom Out")
    main_window.reset_zoom_button = QPushButton("Reset Zoom")
    
    main_window.zoom_layout.addWidget(main_window.zoom_in_button)
    main_window.zoom_layout.addWidget(main_window.zoom_out_button)
    main_window.zoom_layout.addWidget(main_window.reset_zoom_button)
    
    layout.addLayout(main_window.zoom_layout)

    # Esconder os botões de zoom inicialmente
    main_window.zoom_in_button.hide()
    main_window.zoom_out_button.hide()
    main_window.reset_zoom_button.hide()

    # Conectar os botões de zoom às funções
    main_window.zoom_in_button.clicked.connect(lambda: zoom_image(main_window, 1.25))  # Aumentar zoom em 25%
    main_window.zoom_out_button.clicked.connect(lambda: zoom_image(main_window, 0.8))   # Reduzir zoom em 20%
    main_window.reset_zoom_button.clicked.connect(lambda: reset_zoom(main_window))      # Resetar o zoom para o padrão

    main_window.zoom_factor = 1.0  # Definir fator de zoom inicial como 1.0 (100%)

    media_player_tab.setLayout(layout)
    main_window.media_player_tab = media_player_tab
    main_window.tabs.addTab(media_player_tab, "Media Player")

    # Instanciar o player VLC com áudio
    main_window.vlc_instance = vlc.Instance()
    main_window.vlc_player = main_window.vlc_instance.media_player_new()

    # Função para atualizar as informações da mídia
    main_window.update_media_player = lambda: update_media_player(main_window)





def zoom_image(main_window, factor):
    """Ajusta o fator de zoom e redimensiona o PDF ou imagem mantendo a qualidade."""
    if hasattr(main_window, 'original_pixmap') and main_window.original_pixmap:
        main_window.zoom_factor *= factor  # Atualiza o fator de zoom

        # Redimensionar a imagem de acordo com o novo fator de zoom
        scaled_pixmap = main_window.original_pixmap.scaled(
            int(main_window.original_pixmap.width() * main_window.zoom_factor),
            int(main_window.original_pixmap.height() * main_window.zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Atualizar o QLabel com a imagem redimensionada
        main_window.image_label.setPixmap(scaled_pixmap)
        main_window.image_label.adjustSize()  # Ajusta o QLabel ao novo tamanho da imagem
    else:
        QMessageBox.warning(main_window, "Aviso", "Nenhuma imagem foi carregada para aplicar o zoom.")


def reset_zoom(main_window):
    """Redefine o fator de zoom para o valor inicial e redimensiona a imagem."""
    main_window.zoom_factor = 1.0  # Redefine o zoom para o valor inicial (100%)

    if main_window.original_pixmap:  # Verificar se há uma imagem original armazenada
        # Redimensiona a imagem de volta ao tamanho original
        main_window.image_label.setPixmap(main_window.original_pixmap)
        main_window.image_label.adjustSize()  # Ajusta o QLabel ao tamanho original da imagem


def update_media_player(main_window):
    clear_media(main_window)

    if main_window.selected_media_file:
        file_path = main_window.selected_media_file
        file_name = main_window.selected_media_name

        main_window.media_file_label.setText(f"Arquivo: {file_name}")
        print(f"Caminho completo do arquivo criptografado: {file_path}")

        display_media(main_window, file_path, file_name)
    else:
        main_window.media_file_label.setText("Nenhum arquivo selecionado")


def get_resumido_caminho(caminho_completo):
    if len(caminho_completo) > 50:
        return caminho_completo[:25] + '...' + caminho_completo[-20:]
    return caminho_completo


def display_media(main_window, file_path, file_name):
    try:
        base_key = main_window.key_input.text()
        password = main_window.password_input.text()

        if not password:
            QMessageBox.warning(main_window, "Erro", "Por favor, insira uma senha de criptografia.")
            return

        derived_key = derive_key_from_password(password, base_key)
        cipher = Fernet(derived_key)

        with open(file_path, 'rb') as file:
            encrypted_data = file.read()
            decrypted_data = cipher.decrypt(encrypted_data)

        main_window.original_file_path = file_path
        temp_media_file = tempfile.NamedTemporaryFile(delete=False)
        temp_media_file.write(decrypted_data)
        temp_media_file.close()

        if is_image(file_name):
            display_image(main_window, temp_media_file.name)
        elif is_video(file_name):
            display_video_vlc(main_window, temp_media_file.name)
        elif is_audio(file_name):
            display_audio_vlc(main_window, temp_media_file.name)  # Adicionando suporte para áudio
        elif is_pdf(file_name):
            display_pdf(main_window, temp_media_file.name)
        else:
            display_text_file(main_window, main_window.original_file_path, decrypted_data)

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao exibir a mídia: {str(e)}")




def is_pdf(file_name):
    return file_name.lower().endswith('.pdf')


def is_image(file_name):
    return file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))


def is_video(file_name):
    return file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))

def is_audio(file_name):
    return file_name.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.aac'))


def display_image(main_window, file_path):
    try:
        clear_controls(main_window)  # Remover controles anteriores

        pixmap = QPixmap(file_path)

        # Armazenar o pixmap original
        main_window.original_pixmap = pixmap

        # Definir o pixmap no image_label que está dentro da scroll_area
        main_window.image_label.setPixmap(pixmap)
        main_window.image_label.adjustSize()  # Ajustar o tamanho para a imagem

        # Mostrar o image_label, a scroll_area, e os botões de zoom. Esconder o widget de vídeo
        main_window.image_label.show()
        main_window.scroll_area.show()

        # Mostrar os botões de zoom
        main_window.zoom_in_button.show()
        main_window.zoom_out_button.show()
        main_window.reset_zoom_button.show()

        main_window.video_widget.hide()  # Esconder o vídeo quando uma imagem for exibida

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(lambda: clear_media(main_window))
        main_window.controls_layout.addWidget(close_button)

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao exibir a imagem: {str(e)}")









from PyQt6.QtCore import QTimer
def display_video_vlc(main_window, file_path):
    try:
        media = main_window.vlc_instance.media_new(file_path)
        main_window.vlc_player.set_media(media)

        # Associa o vídeo ao widget correto na interface
        win_id = int(main_window.video_widget.winId())
        main_window.vlc_player.set_hwnd(win_id)

        # Tentar iniciar a reprodução de áudio e vídeo
        try:
            main_window.vlc_player.audio_output_device_enum()  # Tentar obter dispositivos de áudio
            main_window.vlc_player.play()
        except Exception as e:
            print(f"Erro de áudio ignorado: {e}")
            main_window.vlc_player.play()  # Continua com o vídeo mesmo sem áudio

        # Esconder outras mídias
        main_window.scroll_area.hide()  # Ocultar a área de imagem e PDFs
        main_window.image_label.hide()  # Ocultar o QLabel de imagem
        main_window.zoom_in_button.hide()
        main_window.zoom_out_button.hide()
        main_window.reset_zoom_button.hide()  # Ocultar os botões de zoom

        main_window.video_widget.setText("")  # Limpar o texto do widget de vídeo
        main_window.video_widget.show()

        # Slider para controle do tempo do vídeo
        if not hasattr(main_window, 'video_slider'):
            main_window.video_slider = QSlider(Qt.Orientation.Horizontal)
            main_window.video_slider.setRange(0, 1000)
        
        main_window.video_slider.show()  # Mostrar o slider

        # Criar os botões de controle do vídeo se não existirem
        if not hasattr(main_window, 'play_button'):
            main_window.play_button = QPushButton("Play")
            main_window.pause_button = QPushButton("Pause")
            main_window.exit_button = QPushButton("Exit")
        
        # Adicionar as funções aos botões
        main_window.play_button.clicked.connect(lambda: main_window.vlc_player.play())
        main_window.pause_button.clicked.connect(lambda: main_window.vlc_player.pause())
        main_window.exit_button.clicked.connect(lambda: close_video(main_window))  # Função para fechar o vídeo

        # Mostrar os botões de controle do vídeo
        main_window.play_button.show()
        main_window.pause_button.show()
        main_window.exit_button.show()

        # Adicionar os botões ao layout de controle se eles ainda não estiverem no layout
        if main_window.controls_layout.count() == 0:
            layout_with_slider = QVBoxLayout()  # Cria um layout vertical para organizar o slider acima dos botões
            layout_with_slider.addWidget(main_window.video_slider)

            buttons_layout = QHBoxLayout()
            buttons_layout.addWidget(main_window.play_button)
            buttons_layout.addWidget(main_window.pause_button)
            buttons_layout.addWidget(main_window.exit_button)

            layout_with_slider.addLayout(buttons_layout)
            main_window.controls_layout.addLayout(layout_with_slider)

        # Conectar o slider ao evento de mudança de tempo
        main_window.video_slider.sliderReleased.connect(lambda: set_video_time(main_window))
        main_window.vlc_player.event_manager().event_attach(vlc.EventType.MediaPlayerTimeChanged, lambda event: update_video_slider(main_window))

        # Configurar o timer para monitorar o progresso do vídeo
        main_window.video_timer = QTimer(main_window)
        main_window.video_timer.timeout.connect(lambda: check_video_end(main_window))
        main_window.video_timer.start(1000)  # Verificar a cada 1 segundo

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao reproduzir o vídeo com VLC: {str(e)}")



def close_video(main_window):
    """Função para fechar o vídeo e esconder a interface do vídeo."""
    main_window.vlc_player.stop()  # Parar o vídeo
    main_window.vlc_player.set_media(None)  # Remover o vídeo carregado

    # Esconder a interface do vídeo e limpar o widget
    main_window.video_widget.hide()
    main_window.video_widget.clear()

    # Esconder o slider de controle do vídeo se estiver visível
    if hasattr(main_window, 'video_slider'):
        main_window.video_slider.hide()

    # Esconder os botões de controle do vídeo
    main_window.play_button.hide()
    main_window.pause_button.hide()
    main_window.exit_button.hide()

    # Remover todos os controles adicionais do layout de controle (botões play, pause, slider, etc.)
    clear_controls(main_window)

    # Esconder e limpar qualquer mensagem ou label relacionado ao vídeo
    main_window.media_file_label.setText("Nenhum arquivo selecionado")








def check_video_end(main_window):
    """Verifica se o vídeo terminou e o reinicia automaticamente."""
    if main_window.vlc_player.get_state() == vlc.State.Ended:
        main_window.vlc_player.stop()
        main_window.vlc_player.set_time(0)  # Volta ao início do vídeo
        main_window.vlc_player.play()  # Reinicia o vídeo

def update_video_slider(main_window):
    if main_window.vlc_player is not None:
        video_duration = main_window.vlc_player.get_length()
        current_time = main_window.vlc_player.get_time()

        if video_duration > 0:
            slider_position = int((current_time / video_duration) * 1000)
            main_window.video_slider.setValue(slider_position)


def set_video_time(main_window):
    if main_window.vlc_player is not None:
        video_duration = main_window.vlc_player.get_length()

        if video_duration > 0:
            slider_value = main_window.video_slider.value()
            new_time = int((slider_value / 1000) * video_duration)
            main_window.vlc_player.set_time(new_time)



def display_text_file(main_window, file_path, content):
    try:
        clear_controls(main_window)  # Remover controles anteriores

        main_window.original_file_path = file_path
        main_window.text_edit.setPlainText(content.decode('utf-8'))
        main_window.text_edit.setVisible(True)

        # Esconder os componentes de imagem e vídeo e os botões de zoom
        main_window.scroll_area.hide()  # Esconder a área de rolagem
        main_window.image_label.hide()  # Esconder a imagem
        main_window.zoom_in_button.hide()  # Esconder o botão de zoom in
        main_window.zoom_out_button.hide()  # Esconder o botão de zoom out
        main_window.reset_zoom_button.hide()  # Esconder o botão de reset de zoom
        main_window.video_widget.hide()  # Esconder o vídeo

        # Botão para fechar o arquivo de texto
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(lambda: clear_media(main_window))
        main_window.controls_layout.addWidget(close_button)

        save_button = QPushButton("Salvar")
        save_button.clicked.connect(lambda: save_text_file(main_window))
        main_window.controls_layout.addWidget(save_button)

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao exibir o arquivo de texto: {str(e)}")



def save_text_file(main_window):
    try:
        updated_content = main_window.text_edit.toPlainText().encode('utf-8')
        base_key = main_window.key_input.text()
        password = main_window.password_input.text()

        derived_key = derive_key_from_password(password, base_key)
        cipher = Fernet(derived_key)
        encrypted_data = cipher.encrypt(updated_content)

        file_path = main_window.original_file_path
        with open(file_path, 'wb') as file:
            file.write(encrypted_data)

        if os.path.exists(file_path):
            print(f"Arquivo salvo com sucesso em: {file_path}")
            print(f"Conteúdo salvo (criptografado): {encrypted_data}")
            print(f"Conteúdo salvo (descriptografado): {updated_content.decode('utf-8')}")
            QMessageBox.information(main_window, "Salvo", "Arquivo salvo com sucesso.")
        else:
            raise IOError("Falha ao salvar o arquivo.")

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao salvar o arquivo: {str(e)}")
        print(f"Erro ao salvar o arquivo: {str(e)}")


def clear_media(main_window):
    main_window.media_file_label.setText("Nenhum arquivo selecionado")

    # Limpar e esconder o QLabel de imagem
    main_window.image_label.clear()
    main_window.image_label.hide()

    # Limpar e esconder o vídeo
    main_window.video_widget.clear()
    main_window.video_widget.hide()

    # Limpar e esconder o campo de texto
    main_window.text_edit.clear()
    main_window.text_edit.setVisible(False)

    # Esconder os botões de zoom quando a mídia for removida
    main_window.zoom_in_button.hide()
    main_window.zoom_out_button.hide()
    main_window.reset_zoom_button.hide()

    # Esconder o botão de fechar e o contador de páginas
    if hasattr(main_window, 'close_button'):
        main_window.close_button.hide()
    if hasattr(main_window, 'page_label'):
        main_window.page_label.hide()

    # Esconder os controles de vídeo
    if hasattr(main_window, 'video_slider'):
        main_window.video_slider.hide()
    if hasattr(main_window, 'play_button'):
        main_window.play_button.hide()
    if hasattr(main_window, 'pause_button'):
        main_window.pause_button.hide()
    if hasattr(main_window, 'exit_button'):
        main_window.exit_button.hide()

    # Esconder os controles de áudio
    if hasattr(main_window, 'audio_slider'):
        main_window.audio_slider.hide()

    # Limpar os controles adicionais (botões de play, pause, etc.)
    clear_controls(main_window)






def clear_controls(main_window):
    """Remove todos os widgets dentro do layout de controle dinâmico (botões, sliders, etc.)"""
    while main_window.controls_layout.count():
        widget = main_window.controls_layout.takeAt(0).widget()
        if widget is not None:
            widget.deleteLater()

    # Esconder sliders e botões relacionados ao áudio se existirem
    if hasattr(main_window, 'audio_slider'):
        main_window.audio_slider.hide()
    if hasattr(main_window, 'play_button'):
        main_window.play_button.hide()
    if hasattr(main_window, 'pause_button'):
        main_window.pause_button.hide()
    if hasattr(main_window, 'exit_button'):
        main_window.exit_button.hide()


def display_pdf(main_window, file_path):
    try:
        clear_controls(main_window)  # Remover controles anteriores

        # Abre o PDF com PyMuPDF
        main_window.pdf_document = fitz.open(file_path)  # Armazena o documento PDF no main_window
        main_window.current_page_index = 0  # Define o índice da página atual como a primeira
        main_window.zoom_factor = 0.5  # Define um fator de zoom inicial mais distante

        # Criar ou atualizar o QLabel para a exibição da página
        if hasattr(main_window, 'page_label'):
            main_window.page_label.show()  # Exibir o contador de páginas, se já existir
        else:
            main_window.page_label = QLabel(f"Página 1 de {main_window.pdf_document.page_count}")

        # Função para carregar e exibir uma página específica do PDF
        def load_pdf_page(page_index, adjust_zoom=True):
            if 0 <= page_index < main_window.pdf_document.page_count:
                # Renderiza a página atual como uma imagem com qualidade máxima
                pdf_page = main_window.pdf_document.load_page(page_index)
                pix = pdf_page.get_pixmap(dpi=300)  # Usando DPI alto para qualidade máxima

                # Criar um arquivo temporário para salvar a imagem do PDF
                temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
                pix.save(temp_image_path)  # Salva a imagem no caminho temporário

                # Armazenar o pixmap original para uso no zoom
                pixmap = QPixmap(temp_image_path)
                main_window.original_pixmap = pixmap  # Armazenar a imagem original renderizada
                main_window.original_size = pixmap.size()  # Armazenar o tamanho original da imagem

                # Exibir a imagem renderizada no QLabel mantendo a proporção original
                main_window.image_label.setPixmap(pixmap)
                main_window.image_label.setScaledContents(False)  # Desativar o escalonamento automático
                main_window.image_label.adjustSize()  # Ajustar o QLabel ao tamanho da imagem

                # Se for o ajuste inicial, forçar o zoom
                if adjust_zoom:
                    adjust_initial_zoom(main_window)

                # Aplicar o zoom atual à nova página
                apply_zoom(main_window)

                # Atualizar o rótulo da página
                main_window.page_label.setText(f"Página {page_index + 1} de {main_window.pdf_document.page_count}")

        # Exibir a primeira página e aplicar o ajuste de zoom
        load_pdf_page(main_window.current_page_index, adjust_zoom=True)

        # Mostrar o image_label e a área de rolagem, e esconder o widget de vídeo
        main_window.scroll_area.show()
        main_window.image_label.show()

        # Mostrar os botões de zoom
        main_window.zoom_in_button.show()
        main_window.zoom_out_button.show()
        main_window.reset_zoom_button.show()

        main_window.video_widget.hide()  # Esconder o vídeo quando um PDF for exibido

        # Adicionar controles para navegar pelas páginas
        previous_page_button = QPushButton("Página Anterior")
        next_page_button = QPushButton("Próxima Página")

        # Conectar os botões às funções de navegação
        previous_page_button.clicked.connect(lambda: navigate_pdf_page(main_window, -1))
        next_page_button.clicked.connect(lambda: navigate_pdf_page(main_window, 1))

        # Adicionar o rótulo da página e o botão fechar com layout ajustado
        main_window.close_button = QPushButton("Fechar")
        main_window.close_button.clicked.connect(lambda: clear_media(main_window))

        page_layout = QHBoxLayout()
        page_layout.addWidget(main_window.close_button)  # Botão fechar à esquerda
        page_layout.addStretch()  # Adiciona um espaçador flexível
        page_layout.addWidget(main_window.page_label)  # Contador de páginas à direita

        # Adicionar os botões de navegação e o layout da página
        main_window.controls_layout.addWidget(previous_page_button)
        main_window.controls_layout.addWidget(next_page_button)
        main_window.controls_layout.addLayout(page_layout)

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao exibir o PDF: {str(e)}")


def adjust_initial_zoom(main_window):
    """Ajusta o zoom inicial para que o PDF seja exibido inteiro na interface."""
    if main_window.original_pixmap:
        # Tamanho da imagem original
        pixmap_width = main_window.original_pixmap.width()
        pixmap_height = main_window.original_pixmap.height()

        # Tamanho da área disponível para exibição (ScrollArea)
        area_width = main_window.scroll_area.viewport().width()

        # Calcula o fator de escala para caber na largura da área disponível
        scale_factor = area_width / pixmap_width

        # Ajustar o fator de zoom inicial para exibir a página completa
        main_window.zoom_factor = scale_factor

        # Redimensionar a imagem para o novo fator de escala
        scaled_pixmap = main_window.original_pixmap.scaled(
            int(pixmap_width * scale_factor),
            int(pixmap_height * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Exibir a imagem redimensionada
        main_window.image_label.setPixmap(scaled_pixmap)
        main_window.image_label.adjustSize()  # Ajustar o QLabel ao tamanho da imagem


def apply_zoom(main_window):
    """Aplica o fator de zoom atual à página."""
    if main_window.original_pixmap:
        # Redimensionar a imagem de acordo com o fator de zoom atual
        scaled_pixmap = main_window.original_pixmap.scaled(
            int(main_window.original_pixmap.width() * main_window.zoom_factor),
            int(main_window.original_pixmap.height() * main_window.zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Exibir a imagem redimensionada
        main_window.image_label.setPixmap(scaled_pixmap)
        main_window.image_label.adjustSize()  # Ajustar o QLabel ao tamanho da imagem


def force_zoom(main_window):
    """Força um ajuste no zoom para garantir que o layout seja atualizado corretamente."""
    apply_zoom(main_window)  # Aplica o fator de zoom atual

def navigate_pdf_page(main_window, direction):
    """Navega pelas páginas do PDF de acordo com o 'direction', preservando o zoom."""
    new_page_index = main_window.current_page_index + direction
    if 0 <= new_page_index < main_window.pdf_document.page_count:
        main_window.current_page_index = new_page_index
        load_pdf_page(main_window, main_window.current_page_index, adjust_zoom=False)


def load_pdf_page(main_window, page_index, adjust_zoom=True):
    """Carrega e exibe a página especificada do PDF, preservando o fator de zoom."""
    if 0 <= page_index < main_window.pdf_document.page_count:
        pdf_page = main_window.pdf_document.load_page(page_index)
        pix = pdf_page.get_pixmap(dpi=300)  # Usa DPI alto para máxima qualidade

        # Salva a imagem temporariamente
        temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
        pix.save(temp_image_path)

        # Define a imagem no QLabel mantendo a proporção
        pixmap = QPixmap(temp_image_path)
        main_window.original_pixmap = pixmap

        # Ajustar o zoom se necessário
        if adjust_zoom:
            adjust_initial_zoom(main_window)

        # Aplicar o zoom atual à página recém-carregada
        apply_zoom(main_window)

        # Atualiza o texto do rótulo de página
        main_window.page_label.setText(f"Página {page_index + 1} de {main_window.pdf_document.page_count}")




def display_audio_vlc(main_window, file_path):
    try:
        media = main_window.vlc_instance.media_new(file_path)
        main_window.vlc_player.set_media(media)

        # Esconder os elementos visuais, já que o áudio não tem vídeo associado
        main_window.scroll_area.hide()  # Ocultar a área de imagem e PDFs
        main_window.image_label.hide()  # Ocultar o QLabel de imagem
        main_window.video_widget.hide()  # Esconder o widget de vídeo
        main_window.zoom_in_button.hide()
        main_window.zoom_out_button.hide()
        main_window.reset_zoom_button.hide()  # Ocultar os botões de zoom

        # Reproduzir o áudio
        main_window.vlc_player.play()

        # Mostrar os controles de áudio (play, pause, stop)
        if not hasattr(main_window, 'audio_slider'):
            main_window.audio_slider = QSlider(Qt.Orientation.Horizontal)
            main_window.audio_slider.setRange(0, 1000)
        
        main_window.audio_slider.show()  # Mostrar o slider de áudio

        # Criar os botões de controle de áudio se não existirem
        if not hasattr(main_window, 'play_button'):
            main_window.play_button = QPushButton("Play")
            main_window.pause_button = QPushButton("Pause")
            main_window.exit_button = QPushButton("Exit")

        # Adicionar as funções aos botões
        main_window.play_button.clicked.connect(lambda: main_window.vlc_player.play())
        main_window.pause_button.clicked.connect(lambda: main_window.vlc_player.pause())
        main_window.exit_button.clicked.connect(lambda: close_audio(main_window))  # Função para fechar o áudio

        # Mostrar os botões de controle do áudio
        main_window.play_button.show()
        main_window.pause_button.show()
        main_window.exit_button.show()

        # Adicionar os botões ao layout de controle se eles ainda não estiverem no layout
        if main_window.controls_layout.count() == 0:
            layout_with_slider = QVBoxLayout()  # Cria um layout vertical para organizar o slider acima dos botões
            layout_with_slider.addWidget(main_window.audio_slider)

            buttons_layout = QHBoxLayout()
            buttons_layout.addWidget(main_window.play_button)
            buttons_layout.addWidget(main_window.pause_button)
            buttons_layout.addWidget(main_window.exit_button)

            layout_with_slider.addLayout(buttons_layout)
            main_window.controls_layout.addLayout(layout_with_slider)

        # Conectar o slider ao evento de mudança de tempo
        main_window.audio_slider.sliderReleased.connect(lambda: set_audio_time(main_window))
        main_window.vlc_player.event_manager().event_attach(vlc.EventType.MediaPlayerTimeChanged, lambda event: update_audio_slider(main_window))

        # Configurar o timer para monitorar o progresso do áudio
        main_window.audio_timer = QTimer(main_window)
        main_window.audio_timer.timeout.connect(lambda: check_audio_end(main_window))
        main_window.audio_timer.start(1000)  # Verificar a cada 1 segundo

    except Exception as e:
        QMessageBox.critical(main_window, "Erro", f"Erro ao reproduzir o áudio com VLC: {str(e)}")

def close_audio(main_window):
    """Função para fechar o áudio e esconder a interface do áudio."""
    main_window.vlc_player.stop()  # Parar o áudio
    main_window.vlc_player.set_media(None)  # Remover o áudio carregado

    # Esconder os controles de áudio
    if hasattr(main_window, 'audio_slider'):
        main_window.audio_slider.hide()

    main_window.play_button.hide()
    main_window.pause_button.hide()
    main_window.exit_button.hide()

    # Remover todos os controles adicionais do layout de controle
    clear_controls(main_window)

    # Esconder e limpar qualquer mensagem ou label relacionado ao áudio
    main_window.media_file_label.setText("Nenhum arquivo selecionado")

def update_audio_slider(main_window):
    if main_window.vlc_player is not None:
        audio_duration = main_window.vlc_player.get_length()
        current_time = main_window.vlc_player.get_time()

        if audio_duration > 0:
            slider_position = int((current_time / audio_duration) * 1000)
            main_window.audio_slider.setValue(slider_position)

def set_audio_time(main_window):
    if main_window.vlc_player is not None:
        audio_duration = main_window.vlc_player.get_length()

        if audio_duration > 0:
            slider_value = main_window.audio_slider.value()
            new_time = int((slider_value / 1000) * audio_duration)
            main_window.vlc_player.set_time(new_time)

def check_audio_end(main_window):
    """Verifica se o áudio terminou e o reinicia automaticamente."""
    if main_window.vlc_player.get_state() == vlc.State.Ended:
        main_window.vlc_player.stop()
        main_window.vlc_player.set_time(0)  # Volta ao início do áudio
        main_window.vlc_player.play()  # Reinicia o áudio

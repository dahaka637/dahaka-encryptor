# Dahaka Encryptor

## Visão Geral

O **Dahaka Encryptor** é um aplicativo desktop desenvolvido em
**Python** com **PyQt6**, voltado para criptografia e gerenciamento de
arquivos multimídia.\
A ferramenta combina segurança de dados com praticidade, permitindo não
apenas **criptografar e descriptografar** arquivos, mas também
**visualizá-los diretamente** em um player multimídia integrado.

------------------------------------------------------------------------

## Funcionalidades Principais

-   **Criptografia de Arquivos**
    -   Criptografia e descriptografia de arquivos individuais e
        diretórios inteiros.
    -   Preservação da estrutura original de pastas ao criptografar.
-   **Gestão de Chaves**
    -   Geração e salvamento de chaves criptográficas.
    -   Uso de **PBKDF2HMAC** para derivação de chaves seguras a partir
        de senha.
    -   Armazenamento de chave em arquivo JSON para reutilização.
-   **Player Multimídia Integrado**
    -   Suporte a vídeos e áudios via **VLC**.
    -   Visualização de documentos PDF usando **PyMuPDF**.
    -   Visualização de imagens (PNG, JPG etc.).
    -   Edição de arquivos de texto com regravação criptografada.
-   **Interface Moderna**
    -   Desenvolvida com **PyQt6**, com abas modulares para:
        -   Lista de Arquivos
        -   Encriptador
        -   Player Multimídia
    -   Tema escuro aplicado por padrão.

------------------------------------------------------------------------

## Arquitetura do Projeto

O sistema é dividido em módulos independentes, cada um responsável por
uma funcionalidade específica:

-   **`main.py`** → Ponto de entrada da aplicação. Gerencia a interface
    principal em abas e inicializa módulos.
-   **`lista.py`** → Permite navegar em diretórios criptografados,
    descriptografar nomes de arquivos e abrir documentos.
-   **`encriptador.py`** → Gerencia criptografia e descriptografia de
    arquivos, geração e persistência de chaves.
-   **`media.py`** → Player multimídia para vídeos, áudios, imagens,
    PDFs e textos.
-   **`encryption_key.json`** → Armazena chave de criptografia salva
    pelo usuário.
-   **`icone.ico`** → Ícone visual da aplicação.

------------------------------------------------------------------------

## Estrutura de Diretórios

    📂 dahaka-encryptor
     ┣ lista.py -> Módulo responsável pela aba de navegação de diretórios e arquivos criptografados.
     ┣ encriptador.py -> Módulo para criptografia e descriptografia, com gerenciamento de chaves.
     ┣ media.py -> Player multimídia integrado para vídeo, áudio, imagens, PDFs e textos.
     ┣ main.py -> Arquivo inicial que carrega a aplicação PyQt6 e organiza as abas principais.
     ┣ encryption_key.json -> Arquivo de armazenamento da chave de criptografia.
     ┗ icone.ico -> Ícone da aplicação.

------------------------------------------------------------------------

## Tecnologias Utilizadas

-   **Python 3.10+**
-   **PyQt6** (interface gráfica)
-   **Cryptography (Fernet, PBKDF2HMAC)** (segurança e criptografia)
-   **VLC (python-vlc)** (reprodução de mídia)
-   **PyMuPDF (fitz)** (visualização de PDFs)
-   **JSON** (armazenamento de chave)

------------------------------------------------------------------------

## Execução do Projeto

Pré-requisitos: - Python 3.10+ - Instalar dependências:
`bash   pip install pyqt6 cryptography python-vlc pymupdf`

Execução:

``` bash
python main.py
```

------------------------------------------------------------------------

## Segurança

-   O sistema usa derivação de chave via **PBKDF2HMAC** para maior
    robustez contra ataques de força bruta.
-   A chave é salva em `encryption_key.json` para conveniência, mas
    recomenda-se uso em ambiente seguro.
-   Boa prática: nunca compartilhar chaves entre diferentes usuários.

------------------------------------------------------------------------

## Licença

Este projeto está sob o regime **All Rights Reserved (Todos os Direitos
Reservados)**.\
Não é permitido copiar, modificar, distribuir, sublicenciar,
comercializar ou utilizar este código, total ou parcialmente, sem
autorização expressa e por escrito do autor.\
Consulte o arquivo LICENSE para mais detalhes.

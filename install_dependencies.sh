#!/bin/bash

# Verifica se o Python está instalado
if ! command -v python &> /dev/null
then
    echo "Python não está instalado. Por favor, instale o Python antes de continuar."
    exit 1
fi

# Verifica se o venv está disponível
if ! python -m venv --help &> /dev/null
then
    echo "O módulo venv não está disponível no Python."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Em sistemas baseados em Debian/Ubuntu, você pode usar: sudo apt-get install python3-venv"
    elif [[ "$OSTYPE" == "msys" ]]; then
        echo "Em sistemas baseados em Windows, você pode usar: pip install virtualenv"
    fi
    exit 1
fi

# Verifica se o arquivo requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "O arquivo requirements.txt não foi encontrado!"
    exit 1
fi

# Cria o ambiente virtual se ele ainda não existir
if [ ! -d "venv" ]; then
    echo "Criando o ambiente virtual..."
    python -m venv venv
else
    echo "Ambiente virtual já existe."
fi

# Ativa o ambiente virtual
echo "Ativando o ambiente virtual..."
if [[ "$OSTYPE" == "msys" ]]; then
    source venv/Scripts/activate  # Windows
else
    source venv/bin/activate  # Linux/MacOS
fi

echo "Ambiente virtual ativado. Para desativar, use o comando 'deactivate'."

# Instala as dependências do arquivo requirements.txt
echo "Instalando dependências listadas no requirements.txt..."
pip install -r requirements.txt

echo "Dependências instaladas com sucesso!"

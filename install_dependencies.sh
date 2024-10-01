#!/bin/bash

# Verify if dependecies already installed
if [ ! -f "requirements.txt" ]; then
    echo "O arquivo requirements.txt não foi encontrado!"
    exit 1
fi

# Install dependencies listed on requiremenets.txt
pip install -r requirements.txt
echo "Dependências instaladas com sucesso!"
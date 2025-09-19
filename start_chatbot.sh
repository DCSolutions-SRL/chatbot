#!/bin/bash

# Script para iniciar el chatbot de Zabbix
cd /home/matutev/chatbot

# Verificar si ya está ejecutándose
if pgrep -f "python3 main.py" > /dev/null; then
    echo "El chatbot ya está ejecutándose"
    exit 0
fi

# Iniciar el chatbot
echo "Iniciando Zabbix AI Chatbot..."
python3 main.py &

# Guardar PID
echo $! > /tmp/zabbix-chatbot.pid

echo "Chatbot iniciado con PID: $!"
echo "Para detenerlo: kill $(cat /tmp/zabbix-chatbot.pid)"
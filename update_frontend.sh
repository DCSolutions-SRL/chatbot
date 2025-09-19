#!/bin/bash

# Script para actualizar los archivos estáticos del chatbot en nginx

echo "Actualizando archivos estáticos del chatbot..."

# Copiar archivos del proyecto a nginx
sudo cp -r /home/matutev/chatbot/static/* /var/www/zabbix-chatbot/

# Cambiar permisos
sudo chown -R www-data:www-data /var/www/zabbix-chatbot

# Recargar nginx
sudo systemctl reload nginx

echo "Archivos estáticos actualizados correctamente"
echo "El frontend está disponible en: http://localhost"
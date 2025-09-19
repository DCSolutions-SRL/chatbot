# Zabbix AI Chatbot

Chatbot especializado en Zabbix usando Google Gemini AI para proporcionar asistencia inteligente en monitoreo de infraestructura.

## 🚀 Características

- **IA Conversacional**: Usa Google Gemini 2.0 Flash para respuestas contextuales
- **Integración Total**: Acceso completo a la base de datos MySQL de Zabbix
- **Cache Inteligente**: Optimización de rendimiento con cache en memoria
- **API REST**: Endpoints bien documentados con FastAPI
- **Monitoreo**: Endpoints de salud y estadísticas del sistema
- **Logging Completo**: Registro detallado para debugging y auditoría

## 📋 Requisitos

- Python 3.10 o superior
- Acceso a base de datos MySQL de Zabbix
- Clave de API de Google Gemini
- 512MB RAM mínimo (recomendado 1GB)

## 🛠️ Instalación

### 1. Clonar y configurar

```bash
git clone <repository_url>
cd chatbot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Configuración del archivo .env

```env
# Obtener clave API de Gemini en: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=tu_clave_api_aqui

# Configuración de tu base de datos Zabbix
MYSQL_HOST=tu_servidor_mysql
MYSQL_USER=zabbix
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=zabbix
```

## 🚀 Ejecución

### Desarrollo

```bash
python main.py
```

### Producción con Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

El servidor estará disponible en: http://localhost:8000

## 📚 Documentación de la API

Una vez iniciado el servidor, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔌 Endpoints Principales

### Chat
```http
POST /api/v1/chat/message
Content-Type: application/json

{
    "message": "¿Cuántos hosts están con problemas?",
    "session_id": "optional_session_id"
}
```

### Estado del Sistema
```http
GET /api/v1/health
GET /api/v1/zabbix/status
```

### Datos de Zabbix
```http
GET /api/v1/zabbix/hosts?limit=10
GET /api/v1/zabbix/problems?limit=10
```

### Administración
```http
POST /api/v1/admin/cache/clear
```

## 💬 Ejemplos de Uso

El chatbot puede responder consultas como:

### Consultas sobre Hosts
- "¿Cuántos hosts tengo configurados?"
- "Muéstrame los hosts que están caídos"
- "¿Cuál es el estado del servidor web-01?"

### Problemas y Alertas
- "¿Hay problemas activos en el sistema?"
- "Muéstrame las alertas de alta prioridad"
- "¿Qué problemas hay en los últimos 24 horas?"

### Métricas y Monitoreo
- "¿Cómo está el rendimiento del host database-01?"
- "Muéstrame las métricas más recientes"
- "¿Qué triggers están configurados?"

### Configuración
- "¿Cuántos items de monitoreo tengo?"
- "Explícame cómo configurar un trigger"
- "¿Cuáles son las mejores prácticas para monitoreo?"

## 🏗️ Arquitectura

```
zabbixbot/
├── main.py              # Aplicación principal FastAPI
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno (crear desde .env.example)
├── .env.example        # Plantilla de configuración
├── README.md           # Esta documentación
│
├── api/
│   ├── routes.py       # Endpoints de la API REST
│   └── models.py       # Modelos Pydantic para requests/responses
│
├── core/
│   ├── chatbot.py      # Lógica principal del chatbot
│   └── gemini.py       # Cliente de Google Gemini API
│
├── database/
│   ├── connection.py   # Manejo de conexiones MySQL
│   └── queries.py      # Consultas SQL específicas de Zabbix
│
└── config/
    └── settings.py     # Configuración de la aplicación
```

## 🔧 Configuración Avanzada

### Cache
El sistema usa cache en memoria para optimizar las consultas frecuentes:

- **Hosts**: TTL de 5 minutos (configurable)
- **Problemas**: TTL de 1 minuto (configurable)

### Logging
Los logs se guardan en:
- **Consola**: Nivel INFO
- **Archivo**: `zabbix_chatbot.log`

### Base de Datos
El sistema accede directamente a las siguientes tablas de Zabbix:
- `hosts` - Información de hosts
- `problems` - Problemas activos
- `triggers` - Configuración de triggers
- `items` - Elementos de monitoreo
- `alerts` - Historial de alertas
- `history*` - Datos históricos

## 🛡️ Seguridad

### Recomendaciones para Producción

1. **Autenticación**: Implementar autenticación JWT o API keys
2. **CORS**: Configurar orígenes específicos en lugar de "*"
3. **Rate Limiting**: Implementar límites de peticiones
4. **HTTPS**: Usar certificados SSL/TLS
5. **Firewall**: Restringir acceso a la base de datos
6. **Secrets**: Usar gestores de secretos para credenciales

### Usuario de Base de Datos
Crear un usuario específico con permisos de solo lectura:

```sql
CREATE USER 'zabbix_chatbot'@'%' IDENTIFIED BY 'password_seguro';
GRANT SELECT ON zabbix.* TO 'zabbix_chatbot'@'%';
FLUSH PRIVILEGES;
```

## 🔍 Troubleshooting

### Error de Conexión a MySQL
```bash
# Verificar conectividad
mysql -h host -u usuario -p -D zabbix

# Verificar permisos
SHOW GRANTS FOR 'usuario'@'host';
```

### Error de API de Gemini
```bash
# Verificar clave API
curl -H "x-goog-api-key: TU_API_KEY" \
  "https://generativelanguage.googleapis.com/v1/models"
```

### Problemas de Performance
1. Aumentar `MYSQL_POOL_SIZE`
2. Ajustar TTL del cache
3. Usar índices en tablas de Zabbix
4. Monitorear logs de consultas SQL

## 📊 Monitoreo

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Métricas
- Tiempo de respuesta de consultas
- Uso de cache (hit/miss ratio)
- Estado de conexiones a DB y Gemini
- Número de consultas SQL ejecutadas

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico:

1. Revisar logs en `zabbix_chatbot.log`
2. Verificar configuración en `.env`
3. Consultar documentación de APIs:
   - [Zabbix Database Schema](https://www.zabbix.com/documentation/current/manual/appendix/install/db_scripts)
   - [Google Gemini API](https://ai.google.dev/docs)
   - [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🔄 Actualizaciones

### v1.0.0
- Implementación inicial
- Integración con Gemini 2.0 Flash
- Soporte completo para consultas de Zabbix
- Cache inteligente
- API REST completa
- Documentación interactiva

---

**Nota**: Este chatbot está especializado únicamente en Zabbix y rechazará amablemente consultas no relacionadas con monitoreo de infraestructura.
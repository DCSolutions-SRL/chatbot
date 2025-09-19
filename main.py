"""
Archivo principal del chatbot especializado en Zabbix.
"""
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from config.settings import settings
from api.routes import router
from api.models import ErrorResponse


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zabbix_chatbot.log')
    ]
)

# Silenciar logs verbosos de watchfiles
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)
logging.getLogger('uvicorn.error').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    
    Args:
        app (FastAPI): Instancia de la aplicación
    """
    # Startup
    logger.info("Iniciando Zabbix AI Chatbot...")
    
    # Validar configuración
    is_valid, errors = settings.validate_config()
    if not is_valid:
        logger.error(f"Configuración inválida: {errors}")
        raise Exception(f"Configuración inválida: {', '.join(errors)}")
    
    logger.info("Configuración validada exitosamente")
    
    # Probar conexiones
    try:
        from database.connection import db_connection
        if db_connection.test_connection():
            logger.info("Conexión a MySQL establecida")
        else:
            logger.warning("No se pudo conectar a MySQL")
    except Exception as e:
        logger.error(f"Error probando conexión MySQL: {e}")
    
    try:
        from core.gemini import get_gemini_client
        gemini_client = get_gemini_client()
        if gemini_client and gemini_client.test_connection():
            logger.info("Conexión a Gemini API establecida")
        else:
            logger.warning("No se pudo conectar a Gemini API")
    except Exception as e:
        logger.error(f"Error probando conexión Gemini: {e}")
    
    logger.info("Zabbix AI Chatbot iniciado exitosamente")
    
    yield
    
    # Shutdown
    logger.info("Deteniendo Zabbix AI Chatbot...")


# Crear aplicación FastAPI
app = FastAPI(
    title="Zabbix AI Chatbot",
    description="""
    Chatbot especializado en Zabbix usando Google Gemini AI.
    
    Este chatbot puede ayudarte con:
    - Análisis de hosts y su estado
    - Revisión de problemas activos
    - Interpretación de alertas y triggers
    - Consultas sobre métricas históricas
    - Mejores prácticas de monitoreo
    
    **Nota**: Solo responde consultas relacionadas con Zabbix y monitoreo de infraestructura.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(router, prefix="/api/v1")

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Servir la página principal del chatbot."""
    return FileResponse('static/index.html')


@app.get("/chat", include_in_schema=False)
async def chat_page():
    """Servir la página del chatbot."""
    return FileResponse('static/index.html')


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page():
    """Servir la página del dashboard."""
    return FileResponse('static/dashboard.html')


@app.get("/api", include_in_schema=False)
async def api_info():
    """Endpoint raíz de la API con información básica."""
    return {
        "service": "Zabbix AI Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
        "chat_ui": "/"
    }


@app.get("/info")
async def app_info():
    """Información detallada de la aplicación."""
    try:
        from database.connection import db_connection
        db_version = db_connection.get_database_version()
    except Exception:
        db_version = "unknown"
    
    try:
        from core.gemini import get_gemini_client
        gemini_client = get_gemini_client()
        gemini_info = gemini_client.get_model_info() if gemini_client else {}
    except Exception:
        gemini_info = {"error": "not available"}
    
    return {
        "application": {
            "name": "Zabbix AI Chatbot",
            "version": "1.0.0",
            "description": "Chatbot especializado en Zabbix usando Google Gemini AI"
        },
        "database": {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "database": settings.MYSQL_DATABASE,
            "version": db_version
        },
        "ai": {
            "provider": "Google Gemini",
            "model": settings.GEMINI_MODEL,
            "info": gemini_info
        },
        "cache": {
            "ttl_hosts": settings.CACHE_TTL_HOSTS,
            "ttl_problems": settings.CACHE_TTL_PROBLEMS
        }
    }


# Manejador global de errores
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Manejador para HTTPException.
    
    Args:
        request: Request object
        exc: HTTPException object
        
    Returns:
        JSONResponse: Respuesta de error estructurada
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    error_response = ErrorResponse(
        error=exc.detail,
        detail=f"HTTP {exc.status_code}",
        timestamp=None
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Manejador general de excepciones no capturadas.
    
    Args:
        request: Request object
        exc: Exception object
        
    Returns:
        JSONResponse: Respuesta de error
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error="Error interno del servidor",
        detail=str(exc) if settings.DEBUG else "Error interno",
        timestamp=None
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


# Personalizar OpenAPI schema
def custom_openapi():
    """Personaliza el schema OpenAPI."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Zabbix AI Chatbot API",
        version="1.0.0",
        description="""
        API REST para el chatbot especializado en Zabbix.
        
        ## Características
        - Procesamiento de consultas en lenguaje natural
        - Integración con base de datos MySQL de Zabbix
        - Respuestas contextuales usando Google Gemini AI
        - Cache inteligente para optimizar performance
        - Endpoints de salud y monitoreo
        
        ## Autenticación
        Actualmente no requiere autenticación (desarrollo).
        
        ## Rate Limiting
        No implementado (recomendado para producción).
        """,
        routes=app.routes,
    )
    
    # Agregar información adicional
    openapi_schema["info"]["x-logo"] = {
        "url": "https://www.zabbix.com/documentation/current/_media/zabbix_logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def start_server():
    """Inicia el servidor de desarrollo."""
    logger.info(f"Iniciando servidor en {settings.API_HOST}:{settings.API_PORT}")
    
    # Configurar uvicorn con logging reducido
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "WARNING"},
            "uvicorn.error": {"handlers": ["default"], "level": "WARNING"},
            "uvicorn.access": {"handlers": ["default"], "level": "WARNING"},
            "watchfiles.main": {"handlers": ["default"], "level": "WARNING"},
        },
    }
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="warning",  # Cambiar de "info" a "warning"
        access_log=False,     # Desactivar access logs
        log_config=log_config
    )


if __name__ == "__main__":
    start_server()
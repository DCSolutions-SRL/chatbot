"""
Rutas de la API para el chatbot de Zabbix.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.models import (
    ChatRequest, 
    ChatResponse, 
    HealthResponse, 
    ZabbixStatusResponse,
    ErrorResponse,
    CacheClearResponse
)
from core.chatbot import zabbix_chatbot
from database import queries

logger = logging.getLogger(__name__)

# Crear el router principal
router = APIRouter()


def get_timestamp() -> str:
    """Obtiene el timestamp actual en formato ISO."""
    return datetime.utcnow().isoformat() + "Z"


@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest) -> ChatResponse:
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    
    Args:
        request (ChatRequest): Solicitud con el mensaje del usuario
        
    Returns:
        ChatResponse: Respuesta del chatbot con metadata
        
    Raises:
        HTTPException: Si hay error procesando el mensaje
    """
    try:
        logger.info(f"Recibida solicitud de chat: {request.message[:50]}...")
        
        # Procesar mensaje con el chatbot
        result = zabbix_chatbot.process_message(
            message=request.message,
            session_id=request.session_id
        )
        
        # Si hay error en el resultado, retornar error HTTP
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=f"Error procesando mensaje: {result['error']}"
            )
        
        # Crear respuesta
        response = ChatResponse(
            response=result['response'],
            data_sources=result.get('data_sources', []),
            query_time=result['query_time'],
            sql_queries_executed=result.get('sql_queries_executed', []),
            intents_detected=result.get('intents_detected', []),
            session_id=request.session_id
        )
        
        logger.info(f"Respuesta generada exitosamente en {result['query_time']:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en chat_message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Verifica el estado de salud del sistema.
    
    Returns:
        HealthResponse: Estado de todos los componentes
    """
    try:
        logger.info("Ejecutando health check")
        
        # Obtener estado de salud del chatbot
        health_status = zabbix_chatbot.get_health_status()
        
        # Determinar estado general
        overall_status = "ok"
        if health_status['database'] != 'connected' or health_status['gemini'] != 'connected':
            overall_status = "degraded"
        
        response = HealthResponse(
            status=overall_status,
            database=health_status['database'],
            gemini=health_status['gemini'],
            cache_size=health_status['cache_size'],
            timestamp=get_timestamp()
        )
        
        logger.info(f"Health check completado: {overall_status}")
        return response
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        # Retornar estado de error pero no fallar la petición
        return HealthResponse(
            status="error",
            database="unknown",
            gemini="unknown",
            cache_size=0,
            timestamp=get_timestamp()
        )


@router.get("/zabbix/status", response_model=ZabbixStatusResponse)
async def zabbix_status() -> ZabbixStatusResponse:
    """
    Obtiene estadísticas generales del sistema Zabbix.
    
    Returns:
        ZabbixStatusResponse: Estadísticas del sistema
        
    Raises:
        HTTPException: Si hay error obteniendo las estadísticas
    """
    try:
        logger.info("Obteniendo estadísticas de Zabbix")
        
        # Obtener estadísticas del sistema
        stats = queries.get_system_stats()
        
        if not stats:
            raise HTTPException(
                status_code=503,
                detail="No se pudieron obtener las estadísticas de Zabbix"
            )
        
        response = ZabbixStatusResponse(
            total_hosts=stats.get('total_hosts', 0),
            active_problems=stats.get('active_problems', 0),
            recent_alerts=stats.get('recent_alerts', 0),
            total_items=stats.get('total_items', 0),
            total_triggers=stats.get('total_triggers', 0),
            timestamp=get_timestamp()
        )
        
        logger.info(f"Estadísticas obtenidas: {stats}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de Zabbix: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.post("/admin/cache/clear", response_model=CacheClearResponse)
async def clear_cache() -> CacheClearResponse:
    """
    Limpia el cache del chatbot.
    
    Returns:
        CacheClearResponse: Resultado de la operación
    """
    try:
        logger.info("Solicitud de limpieza de cache")
        
        # Limpiar cache
        result = zabbix_chatbot.clear_cache()
        
        if result['status'] == 'error':
            raise HTTPException(
                status_code=500,
                detail=result['message']
            )
        
        response = CacheClearResponse(
            status=result['status'],
            message=result['message']
        )
        
        logger.info("Cache limpiado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando cache: {str(e)}"
        )


@router.get("/zabbix/hosts")
async def get_hosts(limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene lista de hosts de Zabbix.
    
    Args:
        limit (int): Número máximo de hosts a retornar
        
    Returns:
        Dict[str, Any]: Lista de hosts
    """
    try:
        logger.info(f"Obteniendo lista de hosts (limit: {limit})")
        
        hosts = queries.get_all_hosts()
        
        # Limitar resultados
        if limit > 0:
            hosts = hosts[:limit]
        
        return {
            "hosts": hosts,
            "total": len(hosts),
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo hosts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo hosts: {str(e)}"
        )


@router.get("/zabbix/problems")
async def get_problems(limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene lista de problemas activos de Zabbix.
    
    Args:
        limit (int): Número máximo de problemas a retornar
        
    Returns:
        Dict[str, Any]: Lista de problemas
    """
    try:
        logger.info(f"Obteniendo problemas activos (limit: {limit})")
        
        problems = queries.get_active_problems()
        
        # Limitar resultados
        if limit > 0:
            problems = problems[:limit]
        
        return {
            "problems": problems,
            "total": len(problems),
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo problemas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo problemas: {str(e)}"
        )


# Fin del archivo routes.py
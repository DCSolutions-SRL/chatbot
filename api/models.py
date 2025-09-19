"""
Modelos Pydantic para la API del chatbot de Zabbix.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """Modelo para las solicitudes de chat."""
    
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="Mensaje o consulta del usuario sobre Zabbix"
    )
    session_id: Optional[str] = Field(
        None,
        max_length=100,
        description="ID de sesión para tracking (opcional)"
    )
    
    @validator('message')
    def validate_message(cls, v):
        """Valida que el mensaje no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Cuántos hosts están con problemas activos?",
                "session_id": "user123_session456"
            }
        }


class ChatResponse(BaseModel):
    """Modelo para las respuestas de chat."""
    
    response: str = Field(
        ...,
        description="Respuesta generada por el chatbot"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Fuentes de datos consultadas para generar la respuesta"
    )
    query_time: float = Field(
        ...,
        ge=0,
        description="Tiempo total de procesamiento en segundos"
    )
    sql_queries_executed: Optional[List[str]] = Field(
        default_factory=list,
        description="Lista de consultas SQL ejecutadas (para debug)"
    )
    intents_detected: Optional[List[str]] = Field(
        default_factory=list,
        description="Intenciones detectadas en el mensaje del usuario"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión utilizado"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Actualmente hay 3 hosts con problemas activos en el sistema...",
                "data_sources": ["hosts", "problems", "system_stats"],
                "query_time": 1.23,
                "sql_queries_executed": ["get_all_hosts()", "get_active_problems()"],
                "intents_detected": ["hosts", "problems"],
                "session_id": "user123_session456"
            }
        }


class HealthResponse(BaseModel):
    """Modelo para la respuesta de estado de salud."""
    
    status: str = Field(
        ...,
        description="Estado general del sistema"
    )
    database: str = Field(
        ...,
        description="Estado de la conexión a la base de datos"
    )
    gemini: str = Field(
        ...,
        description="Estado de la conexión a Gemini API"
    )
    cache_size: int = Field(
        ge=0,
        description="Número de elementos en cache"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp del check de salud"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "database": "connected",
                "gemini": "connected",
                "cache_size": 5,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ZabbixStatusResponse(BaseModel):
    """Modelo para la respuesta de estado de Zabbix."""
    
    total_hosts: int = Field(
        ge=0,
        description="Número total de hosts activos"
    )
    active_problems: int = Field(
        ge=0,
        description="Número de problemas activos"
    )
    recent_alerts: int = Field(
        ge=0,
        description="Número de alertas recientes (última hora)"
    )
    total_items: Optional[int] = Field(
        ge=0,
        description="Número total de items activos"
    )
    total_triggers: Optional[int] = Field(
        ge=0,
        description="Número total de triggers activos"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp de la consulta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_hosts": 25,
                "active_problems": 3,
                "recent_alerts": 7,
                "total_items": 1250,
                "total_triggers": 180,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    
    error: str = Field(
        ...,
        description="Mensaje de error"
    )
    detail: Optional[str] = Field(
        None,
        description="Detalles adicionales del error"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp del error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Error de conexión a la base de datos",
                "detail": "Connection timeout after 10 seconds",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class CacheClearResponse(BaseModel):
    """Modelo para la respuesta de limpieza de cache."""
    
    status: str = Field(
        ...,
        description="Estado de la operación"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del resultado"
    )
    items_cleared: Optional[int] = Field(
        None,
        ge=0,
        description="Número de elementos eliminados del cache"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Cache limpiado exitosamente",
                "items_cleared": 5
            }
        }


class HostInfo(BaseModel):
    """Modelo para información de un host."""
    
    hostid: int
    host: str
    name: str
    status: int
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "hostid": 10084,
                "host": "web-server-01",
                "name": "Web Server 01",
                "status": 0,
                "error": None
            }
        }


class ProblemInfo(BaseModel):
    """Modelo para información de un problema."""
    
    eventid: int
    objectid: int
    clock: int
    acknowledged: int
    severity: int
    hostname: str
    trigger_description: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "eventid": 12345,
                "objectid": 67890,
                "clock": 1705310400,
                "acknowledged": 0,
                "severity": 3,
                "hostname": "web-server-01",
                "trigger_description": "High CPU utilization on {HOST.NAME}"
            }
        }


class SystemInfo(BaseModel):
    """Modelo para información del sistema."""
    
    version: Optional[str] = None
    uptime: Optional[int] = None
    total_hosts: int = 0
    active_problems: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "6.4.0",
                "uptime": 86400,
                "total_hosts": 25,
                "active_problems": 3
            }
        }
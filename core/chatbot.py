"""
Lógica principal del chatbot especializado en Zabbix.
"""
import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from config.settings import settings
from core.gemini import get_gemini_client
from database import queries

logger = logging.getLogger(__name__)


class SimpleCache:
    """Cache simple en memoria con TTL."""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str, ttl: int) -> Optional[Any]:
        """
        Obtiene un valor del cache si no ha expirado.
        
        Args:
            key (str): Clave del cache
            ttl (int): Tiempo de vida en segundos
            
        Returns:
            Optional[Any]: Valor cacheado o None si no existe o expiró
        """
        if key not in self.cache or key not in self.timestamps:
            return None
        
        # Verificar si el valor ha expirado
        if time.time() - self.timestamps[key] > ttl:
            self.remove(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Almacena un valor en el cache.
        
        Args:
            key (str): Clave del cache
            value (Any): Valor a almacenar
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def remove(self, key: str) -> None:
        """
        Elimina un valor del cache.
        
        Args:
            key (str): Clave a eliminar
        """
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Limpia todo el cache."""
        self.cache.clear()
        self.timestamps.clear()


class ZabbixChatbot:
    """Chatbot especializado en Zabbix con IA."""
    
    def __init__(self):
        """Inicializa el chatbot."""
        self.gemini_client = get_gemini_client()
        self.cache = SimpleCache()
        self.query_patterns = {
            'hosts': [
                r'hosts?', r'servidores?', r'máquinas?', r'equipos?',
                r'sistemas?', r'dispositivos?', r'computers?'
            ],
            'problems': [
                r'problemas?', r'alertas?', r'errores?', r'fallos?',
                r'incidentes?', r'issues?', r'críticos?', r'urgentes?'
            ],
            'triggers': [
                r'triggers?', r'disparadores?', r'activadores?'
            ],
            'items': [
                r'items?', r'métricas?', r'elementos?', r'datos?',
                r'monitoreo', r'mediciones?'
            ],
            'alerts': [
                r'notificaciones?', r'avisos?', r'alertas?'
            ],
            'status': [
                r'estado', r'estatus', r'situación', r'resumen',
                r'overview', r'dashboard', r'disponibilidad'
            ],
            'history': [
                r'histórico', r'historial', r'pasado', r'anterior',
                r'tendencia', r'evolución'
            ],
            'network': [
                r'red', r'network', r'conectividad', r'switch', r'router',
                r'ap', r'access point', r'mikrotik', r'cisco'
            ],
            'infrastructure': [
                r'infraestructura', r'servidores', r'dc-', r'vm-',
                r'esxi', r'vmware', r'hyperv', r'virtualización'
            ],
            'security': [
                r'seguridad', r'firewall', r'forti', r'proxy', r'acceso'
            ],
            'physical': [
                r'físico', r'ascensor', r'pasillo', r'sala', r'huella',
                r'biométrico', r'acceso físico'
            ],
            'business': [
                r'negocio', r'odoo', r'asterisk', r'comunicaciones',
                r'telefonía', r'web', r'aplicaciones'
            ],
            'maintenance': [
                r'mantenimiento', r'programado', r'maintenance',
                r'ventana de mantenimiento'
            ],
            'dcs_specific': [
                r'dcs', r'solutions', r'dinamica', r'comercial', 
                r'administracion', r'operaciones', r'grafana'
            ]
        }
        
        # Hosts específicos conocidos de DCS Solutions
        self.known_dcs_hosts = {
            'servers': [
                'DC-Asterisk', 'DC-HYPERV', 'DCS Monitor', 'DCS ODOO', 
                'ESXi', 'VM-TEST', 'Servidor web dcs.ar', 'ProxyDCS'
            ],
            'network': [
                'AP Administracion', 'AP Comercial', 'AP Operaciones',
                'Forti DC', 'Forti Dinamica', 'HP-Administracion'
            ],
            'monitoring': [
                'Grafana', 'NVR', 'DCS Monitor'
            ],
            'physical_access': [
                'Ascensor', 'Huella ZEM560', 'Pasillo Limpieza',
                'Pasillo administracion', 'Pasillo cafeteria',
                'Sala Reunion', 'Sala operaciones', 'Sala preventas'
            ],
            'external': [
                'PUBLICA IPLAN', 'Chequeo WEB'
            ]
        }
        
        logger.info("ZabbixChatbot inicializado")
    
    def _detect_intent(self, message: str) -> List[str]:
        """
        Detecta la intención del usuario basándose en patrones.
        
        Args:
            message (str): Mensaje del usuario
            
        Returns:
            List[str]: Lista de intenciones detectadas
        """
        message_lower = message.lower()
        detected_intents = []
        
        for intent, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    detected_intents.append(intent)
                    break
        
        # Si no se detecta ninguna intención específica, asumir que es una consulta general
        if not detected_intents:
            detected_intents.append('general')
        
        logger.info(f"Intenciones detectadas: {detected_intents}")
        return detected_intents
    
    def _extract_host_name(self, message: str) -> Optional[str]:
        """
        Extrae el nombre de host del mensaje si está presente.
        
        Args:
            message (str): Mensaje del usuario
            
        Returns:
            Optional[str]: Nombre del host o None
        """
        # Patrones para detectar nombres de host
        patterns = [
            r'host[:\s]+([a-zA-Z0-9\-\.]+)',
            r'servidor[:\s]+([a-zA-Z0-9\-\.]+)',
            r'máquina[:\s]+([a-zA-Z0-9\-\.]+)',
            r'equipo[:\s]+([a-zA-Z0-9\-\.]+)',
            r'([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,})',  # Dominios
            r'([a-zA-Z0-9\-]+)',  # Nombres simples al final
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                return matches[0]
        
        return None
    
    def _get_cached_or_fetch(self, cache_key: str, ttl: int, fetch_function, *args) -> Any:
        """
        Obtiene datos del cache o los obtiene de la base de datos.
        
        Args:
            cache_key (str): Clave del cache
            ttl (int): Tiempo de vida en segundos
            fetch_function: Función para obtener los datos
            *args: Argumentos para la función
            
        Returns:
            Any: Datos obtenidos
        """
        # Intentar obtener del cache
        cached_data = self.cache.get(cache_key, ttl)
        if cached_data is not None:
            logger.info(f"Datos obtenidos del cache: {cache_key}")
            return cached_data
        
        # Obtener de la base de datos
        try:
            data = fetch_function(*args)
            self.cache.set(cache_key, data)
            logger.info(f"Datos obtenidos de BD y cacheados: {cache_key}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para {cache_key}: {e}")
            return []
    
    def _gather_context_data(self, intents: List[str], message: str) -> Dict[str, Any]:
        """
        Recopila datos de contexto basándose en las intenciones detectadas.
        
        Args:
            intents (List[str]): Intenciones detectadas
            message (str): Mensaje original del usuario
            
        Returns:
            Dict[str, Any]: Datos de contexto
        """
        context_data = {}
        sql_queries_executed = []
        
        # Detectar si se menciona un host específico
        host_name = self._extract_host_name(message)
        host_info = None
        
        if host_name:
            host_info = queries.get_host_by_name(host_name)
            if host_info:
                context_data['specific_host'] = host_info
                sql_queries_executed.append(f"get_host_by_name('{host_name}')")
        
        # Recopilar datos según las intenciones
        if 'hosts' in intents or 'general' in intents:
            hosts_data = self._get_cached_or_fetch(
                'all_hosts', 
                settings.CACHE_TTL_HOSTS,
                queries.get_all_hosts
            )
            context_data['hosts'] = hosts_data
            sql_queries_executed.append('get_all_hosts()')
        
        # Hosts específicos de DCS si se detecta intención relacionada
        if 'dcs_specific' in intents or 'infrastructure' in intents:
            dcs_hosts = self._get_cached_or_fetch(
                'dcs_hosts',
                settings.CACHE_TTL_HOSTS,
                queries.get_dcs_specific_hosts
            )
            context_data['dcs_hosts'] = dcs_hosts
            sql_queries_executed.append('get_dcs_specific_hosts()')
        
        # Dispositivos de red si se detecta intención de red
        if 'network' in intents:
            network_devices = queries.get_network_devices()
            context_data['network_devices'] = network_devices
            sql_queries_executed.append('get_network_devices()')
        
        # Problemas y estado crítico
        if 'problems' in intents or 'general' in intents or 'status' in intents:
            problems_data = self._get_cached_or_fetch(
                'active_problems',
                settings.CACHE_TTL_PROBLEMS,
                queries.get_active_problems
            )
            context_data['problems'] = problems_data
            sql_queries_executed.append('get_active_problems()')
            
            # Resumen de alertas críticas
            critical_summary = queries.get_critical_alerts_summary()
            context_data['critical_summary'] = critical_summary
            sql_queries_executed.append('get_critical_alerts_summary()')
            
            # Hosts problemáticos
            problematic_hosts = queries.get_top_problematic_hosts()
            context_data['problematic_hosts'] = problematic_hosts
            sql_queries_executed.append('get_top_problematic_hosts()')
        
        # Estado de disponibilidad de hosts
        if 'status' in intents or 'infrastructure' in intents:
            availability_status = queries.get_host_availability_status()
            context_data['host_availability'] = availability_status
            sql_queries_executed.append('get_host_availability_status()')
        
        # Mantenimientos si se detecta intención relacionada
        if 'maintenance' in intents:
            maintenance_info = queries.get_maintenance_info()
            context_data['maintenance'] = maintenance_info
            sql_queries_executed.append('get_maintenance_info()')
        
        # Organizar hosts por categoría si se solicita
        if 'infrastructure' in intents or 'general' in intents:
            hosts_by_category = queries.get_hosts_by_category()
            context_data['hosts_by_category'] = hosts_by_category
            sql_queries_executed.append('get_hosts_by_category()')
        
        if 'triggers' in intents:
            if host_info:
                triggers_data = queries.get_triggers(host_info['hostid'])
                sql_queries_executed.append(f"get_triggers({host_info['hostid']})")
            else:
                triggers_data = queries.get_triggers()
                sql_queries_executed.append('get_triggers()')
            context_data['triggers'] = triggers_data
        
        if 'items' in intents and host_info:
            items_data = queries.get_items(host_info['hostid'])
            context_data['items'] = items_data
            sql_queries_executed.append(f"get_items({host_info['hostid']})")
        
        if 'alerts' in intents:
            alerts_data = queries.get_alerts_last_24h()
            context_data['alerts'] = alerts_data
            sql_queries_executed.append('get_alerts_last_24h()')
        
        if 'history' in intents:
            if host_info:
                history_data = queries.get_latest_data(host_info['hostid'])
                context_data['latest_data'] = history_data
                sql_queries_executed.append(f"get_latest_data({host_info['hostid']})")
            
            # Eventos recientes
            recent_events = queries.get_recent_events()
            context_data['recent_events'] = recent_events
            sql_queries_executed.append('get_recent_events()')
        
        if 'status' in intents or 'general' in intents:
            stats_data = queries.get_system_stats()
            context_data['system_stats'] = stats_data
            sql_queries_executed.append('get_system_stats()')
        
        # Agregar información contextual sobre DCS Solutions
        context_data['dcs_context'] = {
            'company': 'DCS Solutions SRL',
            'known_hosts': self.known_dcs_hosts,
            'infrastructure_overview': {
                'virtualization': 'VMware ESXi, Hyper-V',
                'communication': 'Asterisk PBX',
                'monitoring': 'Zabbix, Grafana',
                'security': 'FortiGate firewalls',
                'business_apps': 'ODOO ERP'
            }
        }
        
        context_data['sql_queries_executed'] = sql_queries_executed
        
        logger.info(f"Datos de contexto recopilados: {list(context_data.keys())}")
        return context_data
    
    def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            message (str): Mensaje del usuario
            session_id (Optional[str]): ID de sesión para tracking
            
        Returns:
            Dict[str, Any]: Respuesta completa con metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando mensaje: {message[:100]}... (Session: {session_id})")
            
            # Validar el cliente Gemini
            if not self.gemini_client:
                return {
                    'response': 'Lo siento, el servicio de IA no está disponible en este momento. Por favor, intenta más tarde.',
                    'data_sources': [],
                    'query_time': time.time() - start_time,
                    'sql_queries_executed': [],
                    'error': 'Gemini client not available'
                }
            
            # Detectar intenciones
            intents = self._detect_intent(message)
            
            # Recopilar datos de contexto
            context_data = self._gather_context_data(intents, message)
            sql_queries = context_data.pop('sql_queries_executed', [])
            
            # Generar respuesta con Gemini
            response = self.gemini_client.generate_response(message, context_data)
            
            # Determinar fuentes de datos utilizadas
            data_sources = list(context_data.keys())
            
            query_time = time.time() - start_time
            
            result = {
                'response': response,
                'data_sources': data_sources,
                'query_time': query_time,
                'sql_queries_executed': sql_queries,
                'intents_detected': intents
            }
            
            logger.info(f"Mensaje procesado exitosamente en {query_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                'response': f'Lo siento, ocurrió un error procesando tu consulta: {str(e)}',
                'data_sources': [],
                'query_time': time.time() - start_time,
                'sql_queries_executed': [],
                'error': str(e)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de salud del chatbot.
        
        Returns:
            Dict[str, Any]: Estado de salud
        """
        health_status = {
            'chatbot': 'ok',
            'database': 'unknown',
            'gemini': 'unknown',
            'cache_size': len(self.cache.cache)
        }
        
        try:
            # Probar conexión a base de datos
            from database.connection import db_connection
            if db_connection.test_connection():
                health_status['database'] = 'connected'
            else:
                health_status['database'] = 'disconnected'
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
        
        try:
            # Probar conexión a Gemini
            if self.gemini_client and self.gemini_client.test_connection():
                health_status['gemini'] = 'connected'
            else:
                health_status['gemini'] = 'disconnected'
        except Exception as e:
            health_status['gemini'] = f'error: {str(e)}'
        
        return health_status
    
    def clear_cache(self) -> Dict[str, str]:
        """
        Limpia el cache del chatbot.
        
        Returns:
            Dict[str, str]: Resultado de la operación
        """
        try:
            items_before = len(self.cache.cache)
            self.cache.clear()
            logger.info(f"Cache limpiado: {items_before} elementos eliminados")
            return {
                'status': 'success',
                'message': f'Cache limpiado exitosamente. {items_before} elementos eliminados.'
            }
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
            return {
                'status': 'error',
                'message': f'Error limpiando cache: {str(e)}'
            }


# Instancia global del chatbot
zabbix_chatbot = ZabbixChatbot()
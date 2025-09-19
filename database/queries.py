"""
Consultas SQL específicas para la base de datos de Zabbix.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.connection import db_connection

logger = logging.getLogger(__name__)


def get_all_hosts() -> List[Dict[str, Any]]:
    """
    Obtiene todos los hosts activos de Zabbix.
    
    Returns:
        List[Dict[str, Any]]: Lista de hosts con información básica
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.error,
        h.disable_until,
        hg.name as hostgroup_name
    FROM hosts h
    LEFT JOIN hosts_groups hgh ON h.hostid = hgh.hostid
    LEFT JOIN hstgrp hg ON hgh.groupid = hg.groupid
    WHERE h.status = 0 
    AND h.flags = 0
    ORDER BY h.name
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo hosts: {e}")
        return []


def get_active_problems() -> List[Dict[str, Any]]:
    """
    Obtiene todos los problemas activos en Zabbix.
    
    Returns:
        List[Dict[str, Any]]: Lista de problemas activos
    """
    query = """
    SELECT 
        p.eventid,
        p.objectid,
        p.clock,
        p.acknowledged,
        p.severity,
        h.host,
        h.name as hostname,
        t.description as trigger_description,
        t.priority,
        e.name as event_name
    FROM problem p
    JOIN triggers t ON p.objectid = t.triggerid
    JOIN functions f ON t.triggerid = f.triggerid
    JOIN items i ON f.itemid = i.itemid
    JOIN hosts h ON i.hostid = h.hostid
    LEFT JOIN events e ON p.eventid = e.eventid
    WHERE p.source = 0 
    AND p.object = 0
    ORDER BY p.severity DESC, p.clock DESC
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo problemas activos: {e}")
        return []


def get_latest_data(hostid: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los datos más recientes para un host específico.
    
    Args:
        hostid (int): ID del host
        limit (int): Número máximo de resultados
        
    Returns:
        List[Dict[str, Any]]: Lista de datos históricos recientes
    """
    # Consulta para obtener los items más recientes
    query = """
    SELECT 
        i.itemid,
        i.name,
        i.key_,
        i.value_type,
        i.units,
        i.status,
        h.clock,
        h.value,
        h.ns
    FROM items i
    LEFT JOIN (
        SELECT itemid, MAX(clock) as max_clock
        FROM history
        WHERE clock > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))
        GROUP BY itemid
        UNION ALL
        SELECT itemid, MAX(clock) as max_clock
        FROM history_uint
        WHERE clock > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))
        GROUP BY itemid
        UNION ALL
        SELECT itemid, MAX(clock) as max_clock
        FROM history_str
        WHERE clock > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))
        GROUP BY itemid
        UNION ALL
        SELECT itemid, MAX(clock) as max_clock
        FROM history_text
        WHERE clock > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))
        GROUP BY itemid
        UNION ALL
        SELECT itemid, MAX(clock) as max_clock
        FROM history_log
        WHERE clock > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))
        GROUP BY itemid
    ) latest ON i.itemid = latest.itemid
    LEFT JOIN history h ON i.itemid = h.itemid AND h.clock = latest.max_clock
    WHERE i.hostid = %s 
    AND i.status = 0
    AND latest.max_clock IS NOT NULL
    ORDER BY h.clock DESC
    LIMIT %s
    """
    try:
        return db_connection.execute_query(query, (hostid, limit))
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos para host {hostid}: {e}")
        return []


def get_triggers(hostid: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Obtiene triggers para un host específico o todos los triggers.
    
    Args:
        hostid (Optional[int]): ID del host, None para todos los hosts
        
    Returns:
        List[Dict[str, Any]]: Lista de triggers
    """
    base_query = """
    SELECT 
        t.triggerid,
        t.expression,
        t.description,
        t.status,
        t.priority,
        t.state,
        t.error,
        h.host,
        h.name as hostname
    FROM triggers t
    JOIN functions f ON t.triggerid = f.triggerid
    JOIN items i ON f.itemid = i.itemid
    JOIN hosts h ON i.hostid = h.hostid
    WHERE t.flags = 0
    """
    
    if hostid:
        query = base_query + " AND h.hostid = %s ORDER BY t.priority DESC"
        params = (hostid,)
    else:
        query = base_query + " ORDER BY t.priority DESC, h.name"
        params = None
    
    try:
        return db_connection.execute_query(query, params)
    except Exception as e:
        logger.error(f"Error obteniendo triggers: {e}")
        return []


def get_items(hostid: int) -> List[Dict[str, Any]]:
    """
    Obtiene todos los items para un host específico.
    
    Args:
        hostid (int): ID del host
        
    Returns:
        List[Dict[str, Any]]: Lista de items del host
    """
    query = """
    SELECT 
        i.itemid,
        i.name,
        i.key_,
        i.type,
        i.value_type,
        i.units,
        i.status,
        i.state,
        i.error,
        i.delay,
        h.host,
        h.name as hostname
    FROM items i
    JOIN hosts h ON i.hostid = h.hostid
    WHERE i.hostid = %s
    AND i.flags = 0
    ORDER BY i.name
    """
    try:
        return db_connection.execute_query(query, (hostid,))
    except Exception as e:
        logger.error(f"Error obteniendo items para host {hostid}: {e}")
        return []


def get_alerts_last_24h() -> List[Dict[str, Any]]:
    """
    Obtiene todas las alertas de las últimas 24 horas.
    
    Returns:
        List[Dict[str, Any]]: Lista de alertas recientes
    """
    # Calcular timestamp de hace 24 horas
    timestamp_24h_ago = int((datetime.now() - timedelta(hours=24)).timestamp())
    
    query = """
    SELECT 
        a.alertid,
        a.actionid,
        a.eventid,
        a.userid,
        a.clock,
        a.mediatypeid,
        a.sendto,
        a.subject,
        a.message,
        a.status,
        a.retries,
        a.error,
        h.host,
        h.name as hostname,
        u.username
    FROM alerts a
    LEFT JOIN events e ON a.eventid = e.eventid
    LEFT JOIN triggers t ON e.objectid = t.triggerid
    LEFT JOIN functions f ON t.triggerid = f.triggerid
    LEFT JOIN items i ON f.itemid = i.itemid
    LEFT JOIN hosts h ON i.hostid = h.hostid
    LEFT JOIN users u ON a.userid = u.userid
    WHERE a.clock >= %s
    ORDER BY a.clock DESC
    """
    try:
        return db_connection.execute_query(query, (timestamp_24h_ago,))
    except Exception as e:
        logger.error(f"Error obteniendo alertas de las últimas 24 horas: {e}")
        return []


def get_host_by_name(hostname: str) -> Optional[Dict[str, Any]]:
    """
    Busca un host por su nombre.
    
    Args:
        hostname (str): Nombre del host a buscar
        
    Returns:
        Optional[Dict[str, Any]]: Información del host o None si no se encuentra
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.error,
        h.disable_until
    FROM hosts h
    WHERE (h.host LIKE %s OR h.name LIKE %s)
    AND h.status = 0 
    AND h.flags = 0
    LIMIT 1
    """
    try:
        pattern = f"%{hostname}%"
        return db_connection.execute_single_query(query, (pattern, pattern))
    except Exception as e:
        logger.error(f"Error buscando host por nombre '{hostname}': {e}")
        return None


def get_system_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales del sistema Zabbix.
    
    Returns:
        Dict[str, Any]: Estadísticas del sistema
    """
    stats = {
        'total_hosts': 0,
        'active_problems': 0,
        'recent_alerts': 0,
        'total_items': 0,
        'total_triggers': 0
    }
    
    try:
        # Total de hosts activos
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM hosts WHERE status = 0 AND flags = 0"
        )
        if result:
            stats['total_hosts'] = result['count']
        
        # Problemas activos
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM problem WHERE source = 0 AND object = 0"
        )
        if result:
            stats['active_problems'] = result['count']
        
        # Alertas recientes (última hora)
        timestamp_1h_ago = int((datetime.now() - timedelta(hours=1)).timestamp())
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM alerts WHERE clock >= %s",
            (timestamp_1h_ago,)
        )
        if result:
            stats['recent_alerts'] = result['count']
        
        # Total de items activos
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM items WHERE status = 0 AND flags = 0"
        )
        if result:
            stats['total_items'] = result['count']
        
        # Total de triggers activos
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM triggers WHERE status = 0 AND flags = 0"
        )
        if result:
            stats['total_triggers'] = result['count']
            
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del sistema: {e}")
    
    return stats


def search_problems_by_severity(severity: int) -> List[Dict[str, Any]]:
    """
    Busca problemas por nivel de severidad.
    
    Args:
        severity (int): Nivel de severidad (0-5)
        
    Returns:
        List[Dict[str, Any]]: Lista de problemas con esa severidad
    """
    query = """
    SELECT 
        p.eventid,
        p.objectid,
        p.clock,
        p.acknowledged,
        p.severity,
        h.host,
        h.name as hostname,
        t.description as trigger_description,
        t.priority
    FROM problem p
    JOIN triggers t ON p.objectid = t.triggerid
    JOIN functions f ON t.triggerid = f.triggerid
    JOIN items i ON f.itemid = i.itemid
    JOIN hosts h ON i.hostid = h.hostid
    WHERE p.source = 0 
    AND p.object = 0
    AND p.severity = %s
    ORDER BY p.clock DESC
    """
    try:
        return db_connection.execute_query(query, (severity,))
    except Exception as e:
        logger.error(f"Error buscando problemas por severidad {severity}: {e}")
        return []


def get_dcs_specific_hosts() -> List[Dict[str, Any]]:
    """
    Obtiene hosts específicos de DCS Solutions que están activos.
    
    Returns:
        List[Dict[str, Any]]: Lista de hosts específicos de DCS
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.available,
        h.error,
        h.disable_until,
        h.description
    FROM hosts h
    WHERE h.status = 0 
    AND h.flags = 0
    AND (h.name LIKE '%DCS%' 
         OR h.name LIKE '%DC-%' 
         OR h.name LIKE '%Forti%'
         OR h.name LIKE '%HP-%'
         OR h.name LIKE '%AP %'
         OR h.name LIKE '%Ascensor%'
         OR h.name LIKE '%ESXi%'
         OR h.name LIKE '%VM-%'
         OR h.name LIKE '%Pasillo%'
         OR h.name LIKE '%Sala%'
         OR h.name LIKE '%Proxy%'
         OR h.name LIKE '%Monitor%'
         OR h.name LIKE '%ODOO%'
         OR h.name LIKE '%Asterisk%'
         OR h.name LIKE '%HYPERV%'
         OR h.name LIKE '%Grafana%'
         OR h.name LIKE '%NVR%'
         OR h.name LIKE '%Huella%'
         OR h.name LIKE '%Servidor web%'
         OR h.name LIKE '%PUBLICA%')
    ORDER BY h.name
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo hosts específicos de DCS: {e}")
        return []


def get_hosts_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene hosts organizados por categorías.
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: Hosts organizados por categoría
    """
    categories = {
        'infrastructure': [],
        'security': [],
        'network': [],
        'monitoring': [],
        'virtualization': [],
        'communication': [],
        'physical_access': [],
        'business_apps': [],
        'templates': []
    }
    
    try:
        all_hosts = get_all_hosts()
        
        for host in all_hosts:
            name = host.get('name', '').lower()
            
            # Infraestructura y servidores
            if any(keyword in name for keyword in ['dc-', 'servidor', 'hp-', 'dell', 'vm-']):
                categories['infrastructure'].append(host)
            # Seguridad
            elif any(keyword in name for keyword in ['forti', 'proxy', 'firewall']):
                categories['security'].append(host)
            # Red y comunicaciones
            elif any(keyword in name for keyword in ['ap ', 'mikrotik', 'cisco', 'switch']):
                categories['network'].append(host)
            # Monitoreo
            elif any(keyword in name for keyword in ['monitor', 'grafana', 'nvr', 'zabbix']):
                categories['monitoring'].append(host)
            # Virtualización
            elif any(keyword in name for keyword in ['esxi', 'vmware', 'hyperv']):
                categories['virtualization'].append(host)
            # Comunicaciones
            elif any(keyword in name for keyword in ['asterisk', 'telefon']):
                categories['communication'].append(host)
            # Control de acceso físico
            elif any(keyword in name for keyword in ['huella', 'ascensor', 'pasillo', 'sala']):
                categories['physical_access'].append(host)
            # Aplicaciones de negocio
            elif any(keyword in name for keyword in ['odoo', 'web']):
                categories['business_apps'].append(host)
            # Templates
            elif any(keyword in name for keyword in ['template', 'by snmp', 'by http', '{']):
                categories['templates'].append(host)
        
        return categories
    except Exception as e:
        logger.error(f"Error organizando hosts por categoría: {e}")
        return categories


def get_recent_events(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Obtiene eventos recientes de Zabbix.
    
    Args:
        hours (int): Número de horas hacia atrás para buscar eventos
        
    Returns:
        List[Dict[str, Any]]: Lista de eventos recientes
    """
    timestamp_ago = int((datetime.now() - timedelta(hours=hours)).timestamp())
    
    query = """
    SELECT 
        e.eventid,
        e.source,
        e.object,
        e.objectid,
        e.clock,
        e.value,
        e.acknowledged,
        e.ns,
        e.name,
        e.severity,
        h.host,
        h.name as hostname,
        t.description as trigger_description
    FROM events e
    LEFT JOIN triggers t ON e.objectid = t.triggerid AND e.object = 0
    LEFT JOIN functions f ON t.triggerid = f.triggerid
    LEFT JOIN items i ON f.itemid = i.itemid
    LEFT JOIN hosts h ON i.hostid = h.hostid
    WHERE e.clock >= %s
    ORDER BY e.clock DESC
    LIMIT 100
    """
    try:
        return db_connection.execute_query(query, (timestamp_ago,))
    except Exception as e:
        logger.error(f"Error obteniendo eventos recientes: {e}")
        return []


def get_host_availability_status() -> List[Dict[str, Any]]:
    """
    Obtiene el estado de disponibilidad de todos los hosts activos.
    
    Returns:
        List[Dict[str, Any]]: Estado de disponibilidad de hosts
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.available,
        h.error,
        h.errors_from,
        h.disable_until,
        CASE h.available
            WHEN 1 THEN 'Available'
            WHEN 2 THEN 'Not Available'
            ELSE 'Unknown'
        END as availability_status,
        CASE h.status
            WHEN 0 THEN 'Monitored'
            WHEN 1 THEN 'Not Monitored'
            ELSE 'Unknown'
        END as monitoring_status
    FROM hosts h
    WHERE h.flags = 0
    ORDER BY h.available ASC, h.name
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo estado de disponibilidad de hosts: {e}")
        return []


def get_maintenance_info() -> List[Dict[str, Any]]:
    """
    Obtiene información sobre mantenimientos programados.
    
    Returns:
        List[Dict[str, Any]]: Información de mantenimientos
    """
    query = """
    SELECT 
        m.maintenanceid,
        m.name as maintenance_name,
        m.description,
        m.active_since,
        m.active_till,
        m.maintenance_type,
        h.host,
        h.name as hostname,
        CASE 
            WHEN m.active_since <= UNIX_TIMESTAMP() AND m.active_till >= UNIX_TIMESTAMP() 
            THEN 'Active'
            WHEN m.active_since > UNIX_TIMESTAMP() 
            THEN 'Scheduled'
            ELSE 'Completed'
        END as status
    FROM maintenances m
    JOIN maintenances_hosts mh ON m.maintenanceid = mh.maintenanceid
    JOIN hosts h ON mh.hostid = h.hostid
    WHERE m.active_till >= UNIX_TIMESTAMP() - 86400  -- Últimas 24 horas y futuro
    ORDER BY m.active_since DESC
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo información de mantenimientos: {e}")
        return []


def get_top_problematic_hosts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los hosts con más problemas activos.
    
    Args:
        limit (int): Número máximo de hosts a retornar
        
    Returns:
        List[Dict[str, Any]]: Hosts con más problemas
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name as hostname,
        COUNT(p.eventid) as problem_count,
        MAX(p.severity) as max_severity,
        h.available,
        h.status
    FROM hosts h
    LEFT JOIN items i ON h.hostid = i.hostid
    LEFT JOIN functions f ON i.itemid = f.itemid
    LEFT JOIN triggers t ON f.triggerid = t.triggerid
    LEFT JOIN problem p ON t.triggerid = p.objectid AND p.source = 0 AND p.object = 0
    WHERE h.status = 0 AND h.flags = 0
    GROUP BY h.hostid, h.host, h.name, h.available, h.status
    HAVING problem_count > 0
    ORDER BY problem_count DESC, max_severity DESC
    LIMIT %s
    """
    try:
        return db_connection.execute_query(query, (limit,))
    except Exception as e:
        logger.error(f"Error obteniendo hosts problemáticos: {e}")
        return []


def search_hosts_by_pattern(pattern: str) -> List[Dict[str, Any]]:
    """
    Busca hosts que coincidan con un patrón específico.
    
    Args:
        pattern (str): Patrón de búsqueda
        
    Returns:
        List[Dict[str, Any]]: Hosts que coinciden con el patrón
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.available,
        h.error,
        h.description,
        CASE h.available
            WHEN 1 THEN 'Available'
            WHEN 2 THEN 'Not Available'
            ELSE 'Unknown'
        END as availability_status
    FROM hosts h
    WHERE h.flags = 0
    AND (h.host LIKE %s OR h.name LIKE %s OR h.description LIKE %s)
    ORDER BY h.name
    """
    try:
        search_pattern = f"%{pattern}%"
        return db_connection.execute_query(query, (search_pattern, search_pattern, search_pattern))
    except Exception as e:
        logger.error(f"Error buscando hosts con patrón '{pattern}': {e}")
        return []


def get_network_devices() -> List[Dict[str, Any]]:
    """
    Obtiene específicamente dispositivos de red monitoreados.
    
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos de red
    """
    query = """
    SELECT 
        h.hostid,
        h.host,
        h.name,
        h.status,
        h.available,
        h.error,
        i.ip,
        i.port,
        i.type as interface_type
    FROM hosts h
    LEFT JOIN interface i ON h.hostid = i.hostid AND i.main = 1
    WHERE h.flags = 0
    AND (h.name LIKE '%Switch%' 
         OR h.name LIKE '%Router%'
         OR h.name LIKE '%AP %'
         OR h.name LIKE '%MikroTik%'
         OR h.name LIKE '%Cisco%'
         OR h.name LIKE '%Forti%'
         OR h.name LIKE 'AP %'
         OR h.name LIKE '%by SNMP%')
    ORDER BY h.name
    """
    try:
        return db_connection.execute_query(query)
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos de red: {e}")
        return []


def get_critical_alerts_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de alertas críticas del sistema.
    
    Returns:
        Dict[str, Any]: Resumen de alertas críticas
    """
    summary = {
        'critical_problems': 0,
        'high_problems': 0,
        'unavailable_hosts': 0,
        'disabled_hosts': 0,
        'recent_alerts': 0,
        'maintenance_active': 0
    }
    
    try:
        # Problemas críticos (severity 5)
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM problem WHERE source = 0 AND object = 0 AND severity = 5"
        )
        if result:
            summary['critical_problems'] = result['count']
        
        # Problemas altos (severity 4)
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM problem WHERE source = 0 AND object = 0 AND severity = 4"
        )
        if result:
            summary['high_problems'] = result['count']
        
        # Hosts no disponibles
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM hosts WHERE available = 2 AND status = 0 AND flags = 0"
        )
        if result:
            summary['unavailable_hosts'] = result['count']
        
        # Hosts deshabilitados
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM hosts WHERE status = 1 AND flags = 0"
        )
        if result:
            summary['disabled_hosts'] = result['count']
        
        # Alertas recientes (última hora)
        timestamp_1h_ago = int((datetime.now() - timedelta(hours=1)).timestamp())
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM alerts WHERE clock >= %s",
            (timestamp_1h_ago,)
        )
        if result:
            summary['recent_alerts'] = result['count']
        
        # Mantenimientos activos
        current_timestamp = int(datetime.now().timestamp())
        result = db_connection.execute_single_query(
            "SELECT COUNT(*) as count FROM maintenances WHERE active_since <= %s AND active_till >= %s",
            (current_timestamp, current_timestamp)
        )
        if result:
            summary['maintenance_active'] = result['count']
            
    except Exception as e:
        logger.error(f"Error obteniendo resumen de alertas críticas: {e}")
    
    return summary
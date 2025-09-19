"""
Manejo de conexiones a la base de datos MySQL de Zabbix.
"""
import logging
import pymysql
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from pymysql.cursors import DictCursor
from config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Clase para manejar conexiones a la base de datos MySQL de Zabbix."""
    
    def __init__(self):
        """Inicializa la configuración de conexión."""
        self.config = {
            'host': settings.MYSQL_HOST,
            'port': settings.MYSQL_PORT,
            'user': settings.MYSQL_USER,
            'password': settings.MYSQL_PASSWORD,
            'database': settings.MYSQL_DATABASE,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': True,
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30
        }
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos.
        
        Yields:
            pymysql.Connection: Conexión activa a la base de datos
        """
        connection = None
        try:
            connection = pymysql.connect(**self.config)
            logger.info("Conexión a MySQL establecida exitosamente")
            yield connection
        except pymysql.Error as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.info("Conexión a MySQL cerrada")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SELECT y retorna los resultados.
        
        Args:
            query (str): Consulta SQL a ejecutar
            params (Optional[tuple]): Parámetros para la consulta
            
        Returns:
            List[Dict[str, Any]]: Lista de resultados como diccionarios
            
        Raises:
            Exception: Si hay error en la consulta
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    # Registrar la consulta para debug
                    logger.info(f"Ejecutando consulta: {query}")
                    if params:
                        logger.info(f"Parámetros: {params}")
                    
                    # Ejecutar la consulta
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    logger.info(f"Consulta ejecutada exitosamente. Resultados: {len(results)} filas")
                    return results
                    
        except pymysql.Error as e:
            logger.error(f"Error ejecutando consulta: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise Exception(f"Error en la base de datos: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise
    
    def execute_single_query(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Ejecuta una consulta que se espera retorne un solo resultado.
        
        Args:
            query (str): Consulta SQL a ejecutar
            params (Optional[tuple]): Parámetros para la consulta
            
        Returns:
            Optional[Dict[str, Any]]: Resultado como diccionario o None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Error probando conexión: {e}")
            return False
    
    def get_database_version(self) -> Optional[str]:
        """
        Obtiene la versión de MySQL.
        
        Returns:
            Optional[str]: Versión de MySQL o None si hay error
        """
        try:
            result = self.execute_single_query("SELECT VERSION() as version")
            return result['version'] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo versión de base de datos: {e}")
            return None
    
    def get_zabbix_config(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica de configuración de Zabbix.
        
        Returns:
            Optional[Dict[str, Any]]: Información de configuración o None
        """
        try:
            query = """
            SELECT 
                COUNT(*) as total_hosts
            FROM hosts 
            WHERE status = 0 AND available != 2
            """
            result = self.execute_single_query(query)
            return result
        except Exception as e:
            logger.error(f"Error obteniendo configuración de Zabbix: {e}")
            return None


# Instancia global de la conexión a la base de datos
db_connection = DatabaseConnection()
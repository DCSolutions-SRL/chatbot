"""
Configuración del sistema usando variables de entorno.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()


class Settings:
    """Configuración del sistema usando variables de entorno."""
    
    # Configuración de Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Configuración de MySQL para Zabbix
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "zabbix")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "zabbix")
    
    # Configuración del servidor
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Configuración de cache
    CACHE_TTL_HOSTS: int = int(os.getenv("CACHE_TTL_HOSTS", "300"))  # 5 minutos
    CACHE_TTL_PROBLEMS: int = int(os.getenv("CACHE_TTL_PROBLEMS", "60"))  # 1 minuto
    
    # Pool de conexiones MySQL
    MYSQL_POOL_SIZE: int = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    MYSQL_MAX_OVERFLOW: int = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Valida que todas las configuraciones requeridas estén presentes.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY es requerida")
            
        if not self.MYSQL_PASSWORD:
            errors.append("MYSQL_PASSWORD es requerida")
            
        if not self.MYSQL_HOST:
            errors.append("MYSQL_HOST es requerido")
            
        if not self.MYSQL_USER:
            errors.append("MYSQL_USER es requerido")
            
        if not self.MYSQL_DATABASE:
            errors.append("MYSQL_DATABASE es requerido")
        
        return len(errors) == 0, errors
    
    def get_mysql_url(self) -> str:
        """
        Construye la URL de conexión a MySQL.
        
        Returns:
            str: URL de conexión MySQL
        """
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


# Instancia global de configuración
settings = Settings()
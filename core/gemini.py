"""
Cliente para integración con Google Gemini API.
"""
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Cliente para interactuar con Google Gemini API."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el cliente de Gemini.
        
        Args:
            api_key (str): Clave de API de Google Gemini
        """
        self.api_key = api_key
        self.model_name = settings.GEMINI_MODEL
        
        # Configurar la API
        genai.configure(api_key=api_key)
        
        # Inicializar el modelo
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Cliente Gemini inicializado con modelo: {self.model_name}")
        except Exception as e:
            logger.error(f"Error inicializando modelo Gemini: {e}")
            raise
    
    def _format_context_data(self, context_data: Dict[str, Any]) -> str:
        """
        Formatea los datos de contexto para incluir en el prompt.
        
        Args:
            context_data (Dict[str, Any]): Datos de contexto de Zabbix
            
        Returns:
            str: Datos formateados para el prompt
        """
        if not context_data:
            return "No hay datos de contexto disponibles."
        
        try:
            # Formatear los datos de manera legible
            formatted_data = []
            
            for key, value in context_data.items():
                if isinstance(value, list) and value:
                    formatted_data.append(f"\n{key.upper()}:")
                    for i, item in enumerate(value[:5]):  # Limitar a 5 elementos por tipo
                        if isinstance(item, dict):
                            # Mostrar solo los campos más relevantes
                            relevant_fields = self._extract_relevant_fields(key, item)
                            formatted_data.append(f"  - {relevant_fields}")
                        else:
                            formatted_data.append(f"  - {item}")
                    
                    if len(value) > 5:
                        formatted_data.append(f"  ... y {len(value) - 5} elementos más")
                
                elif isinstance(value, dict):
                    formatted_data.append(f"\n{key.upper()}:")
                    for sub_key, sub_value in value.items():
                        formatted_data.append(f"  {sub_key}: {sub_value}")
                
                else:
                    formatted_data.append(f"{key}: {value}")
            
            return "\n".join(formatted_data)
            
        except Exception as e:
            logger.error(f"Error formateando datos de contexto: {e}")
            return f"Error formateando datos: {str(e)}"
    
    def _extract_relevant_fields(self, data_type: str, item: Dict[str, Any]) -> str:
        """
        Extrae los campos más relevantes según el tipo de datos.
        
        Args:
            data_type (str): Tipo de datos (hosts, problems, etc.)
            item (Dict[str, Any]): Elemento de datos
            
        Returns:
            str: Campos relevantes formateados
        """
        if data_type == "hosts":
            return f"Host: {item.get('name', item.get('host', 'N/A'))}, Status: {item.get('status', 'N/A')}, Available: {item.get('available', 'N/A')}"
        
        elif data_type == "problems":
            return f"Host: {item.get('hostname', 'N/A')}, Trigger: {item.get('trigger_description', 'N/A')}, Severity: {item.get('severity', 'N/A')}"
        
        elif data_type == "triggers":
            return f"Host: {item.get('hostname', 'N/A')}, Description: {item.get('description', 'N/A')}, Priority: {item.get('priority', 'N/A')}"
        
        elif data_type == "items":
            return f"Name: {item.get('name', 'N/A')}, Key: {item.get('key_', 'N/A')}, Status: {item.get('status', 'N/A')}"
        
        elif data_type == "alerts":
            return f"Host: {item.get('hostname', 'N/A')}, Subject: {item.get('subject', 'N/A')}, Status: {item.get('status', 'N/A')}"
        
        else:
            # Para otros tipos, mostrar los primeros 3 campos
            fields = list(item.items())[:3]
            return ", ".join([f"{k}: {v}" for k, v in fields])
    
    def _create_prompt(self, user_query: str, context_data: Dict[str, Any]) -> str:
        """
        Crea el prompt completo para Gemini.
        
        Args:
            user_query (str): Consulta del usuario
            context_data (Dict[str, Any]): Datos de contexto de Zabbix
            
        Returns:
            str: Prompt completo
        """
        formatted_context = self._format_context_data(context_data)
        
        prompt = f"""Eres un asistente experto en Zabbix especializado en el monitoreo de infraestructura de DCS Solutions SRL. 

INFORMACIÓN DE LA EMPRESA:
- Nombre: DCS Solutions SRL  
- Infraestructura: Servidores Windows/Linux, virtualización VMware ESXi e Hyper-V
- Servicios: Telefonía Asterisk, ERP ODOO, sistemas de monitoreo Zabbix/Grafana
- Seguridad: Firewalls FortiGate, control de acceso físico
- Red: Access Points, switches MikroTik/Cisco, conectividad IPLAN

HOSTS PRINCIPALES MONITOREADOS:
- Servidores: DC-Asterisk, DC-HYPERV, DCS Monitor, DCS ODOO, ESXi, VM-TEST
- Red: AP Administracion, AP Comercial, AP Operaciones, Forti DC, Forti Dinamica  
- Monitoreo: Grafana, NVR, DCS Monitor
- Acceso físico: Ascensor, Huella ZEM560, salas y pasillos
- Externos: PUBLICA IPLAN, Servidor web dcs.ar

DATOS ACTUALES DEL SISTEMA ZABBIX:
{formatted_context}

PREGUNTA DEL USUARIO: {user_query}

REGLAS IMPORTANTES:
1. Responde ÚNICAMENTE sobre temas relacionados con Zabbix, monitoreo de infraestructura y los sistemas de DCS Solutions
2. Si preguntan algo no relacionado con Zabbix/monitoreo, indica amablemente que solo puedes ayudar con temas de Zabbix
3. Usa los datos proporcionados para dar respuestas precisas y específicas sobre la infraestructura de DCS
4. Conoce los hosts específicos de DCS y sus funciones (servidores, red, monitoreo, acceso físico)
5. Si hay problemas activos, priorízalos en tu respuesta e indica el impacto en los servicios de DCS
6. Proporciona recomendaciones específicas para el entorno de DCS Solutions
7. Si mencionan hosts específicos (DC-Asterisk, Forti DC, etc.), usa ese contexto
8. Responde en español de manera profesional y técnica

FORMATO DE RESPUESTA:
- Sé conciso pero completo
- Usa bullet points cuando sea apropiado  
- Incluye valores específicos de los datos cuando sea relevante
- Si hay alertas críticas, mencionarlas primero con el impacto en servicios
- Contextualiza las respuestas al entorno específico de DCS Solutions"""

        return prompt
    
    def generate_response(self, user_query: str, context_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Genera una respuesta usando Gemini API.
        
        Args:
            user_query (str): Consulta del usuario
            context_data (Optional[Dict[str, Any]]): Datos de contexto de Zabbix
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Crear el prompt completo
            prompt = self._create_prompt(user_query, context_data or {})
            
            logger.info(f"Generando respuesta para consulta: {user_query[:100]}...")
            logger.debug(f"Prompt completo: {prompt}")
            
            # Configuración de generación
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 2048,
            }
            
            # Generar respuesta
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                logger.warning("Gemini retornó respuesta vacía")
                return "Lo siento, no pude generar una respuesta. Por favor, intenta reformular tu pregunta."
            
            logger.info("Respuesta generada exitosamente")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini: {e}")
            return f"Error generando respuesta: {str(e)}. Por favor, intenta nuevamente."
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Gemini API.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            test_response = self.model.generate_content("Test")
            return test_response.text is not None
        except Exception as e:
            logger.error(f"Error probando conexión con Gemini: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el modelo de Gemini en uso.
        
        Returns:
            Dict[str, Any]: Información del modelo
        """
        try:
            return {
                "model_name": self.model_name,
                "api_configured": self.api_key is not None,
                "connection_test": self.test_connection()
            }
        except Exception as e:
            logger.error(f"Error obteniendo información del modelo: {e}")
            return {
                "model_name": self.model_name,
                "api_configured": False,
                "connection_test": False,
                "error": str(e)
            }


# Instancia global del cliente Gemini
def get_gemini_client() -> Optional[GeminiClient]:
    """
    Obtiene una instancia del cliente Gemini.
    
    Returns:
        Optional[GeminiClient]: Cliente Gemini o None si hay error
    """
    try:
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY no está configurada")
            return None
        
        return GeminiClient(settings.GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Error creando cliente Gemini: {e}")
        return None
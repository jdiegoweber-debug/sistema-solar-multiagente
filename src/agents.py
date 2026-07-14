import os # Manejo de variables de entorno del sistema operativo
import json # Codificación y decodificación de objetos estructurados JSON
from google import genai # El SDK moderno y oficial provisto por Google para el consumo de modelos Gemini
from google.genai import types # Módulos de configuración tipada para parámetros avanzados del chat
from dotenv import load_dotenv # Carga segura de claves de desarrollo desde tu archivo .env

# =========================================================================
# IMPORTACIÓN DE HERRAMIENTAS TÉCNICAS Y COMERCIALES (PROTOCOLO RAG Y MCP)
# =========================================================================
# Cargamos tu motor de búsqueda semántica por similitud coseno basado en embeddings vectoriales
from src.tools.rag_tool import consultar_normativas_solares
# Cargamos tu herramienta MCP simulada para persistir los leads interesados directamente en el CRM
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm

# Inicializamos el entorno extrayendo tu GEMINI_API_KEY configurada localmente
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Resto de tu código intacto (Clase SubAgenteBaseConSesion, instancias de agentes y clase OrquestadorSolar)...

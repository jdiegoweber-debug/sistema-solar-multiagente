import os # Manejo de variables de entorno y rutas del sistema operativo
import json # Codificación y decodificación de datos en formato estructurado JSON
import re # Biblioteca para análisis de expresiones regulares y búsquedas de texto avanzadas
from google import genai # El SDK moderno y oficial de Google para consumir modelos Gemini
from google.genai import types # Configuraciones tipadas avanzadas para los chats de la API
from dotenv import load_dotenv # Carga segura de claves de desarrollo desde el archivo .env

# Importamos las herramientas del sistema
from src.tools.web_reader_tool import leer_contenido_enlace_web
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm
from src.tools.rag_tool import consultar_normativas_solares

# Inicializamos las variables de entorno levantando tu clave privada GEMINI_API_KEY
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Regla global de localización para obligar a los modelos a usar lenguaje local y ocultar la memoria
REGLA_ARGENTINA = (
    "\n\n[REGLA DE LOCALIZACIÓN OBLIGATORIA]: Debes hablar utilizando exclusivamente "
    "el dialecto castellano rioplatense (de Argentina). Trata al usuario de 'vos' (voseo). "
    "Está terminantemente prohibido usar modismos de España o México como 'vale', 'platicar', 'computadora', etc. "
    "Usa expresiones naturales de Argentina como 'dale', 'che', 'contame', 'factura de luz', 'boleta'."
    "\n\n[REGLA DE PRIVACIDAD Y CONTEXTO CRÍTICA]: Tienes acceso a un bloque de datos del cliente llamado 'SharedState'. "
    "Usa esa información internamente para guiar tus respuestas y dar por sentados los datos. "
    "Está TERMINANTEMENTE PROHIBIDO volver a preguntar datos que ya figuren con un valor en el SharedState. "
    "Está prohibido escribir el texto '[SharedState]' o volcar el diccionario JSON en tu respuesta."
)

# Memoria global cruzada de mensajes unificados
HISTORIAL_MENSAJES_GLOBAL = {}

# =========================================================================
# CLASE BASE PARA SUB-AGENTES CON CONTEXTO COMPARTIDO MULTIMODAL
# =========================================================================
class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name 
        self.instruction = instruction + REGLA_ARGENTINA 
        self.tools = tools or [] 

    # ¡CORREGIDO!: Sumamos el parámetro opcional ruta_archivo para sincronizar con main.py
    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default", ruta_archivo=None):
        """
        Gestiona la conversación histórica cruzada inyectando el estado mutado, las herramientas y
        archivos locales (multimodales) directamente a la API de Google.
        """
        global HISTORIAL_MENSAJES_GLOBAL
        
        if session_id not in HISTORIAL_MENSAJES_GLOBAL:
            HISTORIAL_MENSAJES_GLOBAL[session_id] = []

        contexto_herramientas = ""
        
        # 1. Inyección del RAG Técnico
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas += f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
            
        # 2. Inyección del MCP Comercial
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas += f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"

        # 3. Inyección de la Herramienta de Lectura de Enlaces Web (Scraper)
        if leer_contenido_enlace_web in self.tools and ("http://" in mensaje_usuario or "https://" in mensaje_usuario):
            urls = re.findall(r'(https?://[^\s]+)', mensaje_usuario)
            if urls:
                # Invocamos la herramienta web e inyectamos el texto limpio extraído de la página en el prompt
                contexto_herramientas += f"\n\n[Contenido de la Factura Extraído de la Web]: {leer_contenido_enlace_web(urls[0])}"

        # Ensamblamos las partes del mensaje (pueden ser texto o referencias de archivos de Google)
        partes_mensaje = []
        
        # --- BLOQUE MULTIMODAL NATIVO (Procesamiento de Archivos Locales) ---
        if ruta_archivo and os.path.exists(ruta_archivo):
            try:
                print(f"📁 [File Service Cloud] Subiendo '{os.path.basename(ruta_archivo)}' de forma directa a Google...")
                archivo_google = client.files.upload(file=ruta_archivo)
                partes_mensaje.append(archivo_google)
                print("✅ [File Service Cloud] Archivo cargado correctamente en el contexto multimodal.")
            except Exception as e:
                contexto_herramientas += f"\n\n[Aviso del Sistema]: No se pudo cargar el archivo adjunto por el error: {e}"

        # Añadimos el texto final del usuario junto con las inyecciones de las herramientas a las partes
        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"
        partes_mensaje.append(types.Part.from_text(text=mensaje_final))

        # Guardamos el contenido estructurado en la memoria global de la sesión
        HISTORIAL_MENSAJES_GLOBAL[session_id].append(
            types.Content(role="user", parts=partes_mensaje)
        )

        # Configuramos las instrucciones del sistema actualizadas dinámicamente con el estado real mutado
        config = types.GenerateContentConfig(
            system_instruction=f"{self.instruction}\n\n[SharedState Actual de la Memoria Backend]: {datos_cliente}",
            temperature=0.3 
        )

        # Invocamos el modelo generate_content enviándole TODO el historial unificado con soporte multimodal
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=HISTORIAL_MENSAJES_GLOBAL[session_id],
            config=config
        )
        
        respuesta_final = response.text

        # Guardamos la respuesta generada por el agente en el historial global para el próximo turno
        HISTORIAL_MENSAJES_GLOBAL[session_id].append(
            types.Content(role="model", parts=[types.Part.from_text(text=respuesta_final)])
        )
            
        return respuesta_final


# =========================================================================
# INSTANCIAS DE SUB-AGENTES ESPECIALIZADOS
# =========================================================================
subagente_casual = SubAgenteBaseConSesion(
    name="AgenteCasual",
    instruction="Eres un compañero de conversación casual. Responde en 3 oraciones o menos. NO des datos técnicos."
)

subagente_coloquial = SubAgenteBaseConSesion(
    name="AgenteColoquial",
    instruction="Eres un asesor empático para clientes residenciales. Averigua sutilmente los datos que falten del SharedState sin repetir preguntas."
)

subagente_tecnico = SubAgenteBaseConSesion(
    name="AgenteTecnico",
    instruction="Eres un ingeniero fotovoltaico. Responde dudas técnicas basándote obligatoriamente en el RAG inyectado.",
    tools=[consultar_normativas_solares]
)

subagente_comercial = SubAgenteBaseConSesion(
    name="AgenteComercial",
    instruction=(
        "Eres el asesor financiero especialista en costos del equipo solar. Calculas presupuestos estimados y el retorno de inversión (ROI).\n"
        "Analiza el historial y el bloque de contenido o archivo adjunto si existiese: si el cliente te pasa un enlace, lee los datos extraídos "
        "para buscar los kWh consumidos, el monto total a pagar de la boleta y el nombre de la distribuidora (ej: Usina de Tandil).\n"
        "Usa esos números reales de la factura para ajustar el cálculo del ROI en pesos argentinos de forma precisa."
    ),
    tools=[mcp_guardar_cliente_crm, leer_contenido_enlace_web]
)


# =========================================================================
# AGENTE ORQUESTADOR CENTRAL
# =========================================================================
class OrquestadorSolar:
    def __init__(self):
        self.name = "OrquestadorSolar"

    def _extraer_datos_bg(self, user_input, datos_cliente):
        """Aísla la extracción JSON en su propio entorno para que si falla no rompa el enrutamiento."""
        prompt_extractor = f"""
        Extrae datos relevantes (nombre, ciudad, consumo_anual_kwh, tipo_sistema) en un objeto JSON puro.
        Estado actual: {datos_cliente}
        Mensaje: "{user_input}"
        No agregues formato markdown ni texto extra.
        """
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            for k, v in nuevos_datos.items():
                if v is not None:
                    datos_cliente[k] = v
        except Exception:
            pass

    def route_request(self, user_input, datos_cliente):
        """Ejecuta la extracción y garantiza un retorno de agente válido siempre."""
        self._extraer_datos_bg(user_input, datos_cliente)
        mensaje = user_input.lower()

        if any(word in mensaje for word in ["salir", "chau", "adios", "hasta luego", "terminar", "cerrar"]):
            return subagente_casual

        if any(word in mensaje for word in ["precio", "costo", "financiar", "presupuesto", "roi", "plata", "guardar", "crm", "comprar", "calcula", "calculalo", "retorno", "usina", "http", "https", "www", ".com", "adjunto", "archivo", "factura", "boleta", "pdf", "imagen"]):
            return subagente_comercial


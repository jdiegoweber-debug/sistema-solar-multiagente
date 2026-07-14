import os # Manejo de variables de entorno y rutas del sistema operativo
import json # Codificación y decodificación de datos en formato estructurado JSON
import re # Biblioteca para análisis de expresiones regulares y búsquedas de texto avanzadas
from google import genai # El SDK moderno y oficial de Google para consumir modelos Gemini
from google.genai import types # Configuraciones tipadas avanzadas para los chats de la API
from dotenv import load_dotenv # Carga segura de claves de desarrollo desde el archivo .env

# =========================================================================
# IMPORTACIÓN DE HERRAMIENTAS TÉCNICAS Y COMERCIALES (PROTOCOLO RAG Y MCP)
# =========================================================================
from src.tools.rag_tool import consultar_normativas_solares
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm

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

# =========================================================================
# MEMORIA GLOBAL COMPARTIDA DE TURNOS (Aisla y unifica la conversación por sesión)
# =========================================================================
# Diccionario global en memoria para guardar el historial completo de mensajes cruzados entre todos los agentes
HISTORIAL_MENSAJES_GLOBAL = {}

# =========================================================================
# CLASE BASE PARA SUB-AGENTES CON CONTEXTO COMPARTIDO
# =========================================================================
class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name 
        self.instruction = instruction + REGLA_ARGENTINA # Acoplamos la regla a cada agente
        self.tools = tools or [] 

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default"):
        """
        Gestiona la conversación histórica cruzada inyectando el estado mutado y las herramientas RAG/MCP.
        """
        global HISTORIAL_MENSAJES_GLOBAL
        
        # Inicializamos la lista de mensajes cronológicos de la sesión si es la primera interacción
        if session_id not in HISTORIAL_MENSAJES_GLOBAL:
            HISTORIAL_MENSAJES_GLOBAL[session_id] = []

        # Bloque de lógica integrada de ejecución de herramientas para inyectar contexto fresco
        contexto_herramientas = ""
        
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas = f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
            
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas = f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"

        # Ensamblamos el mensaje final sumando el aporte del RAG o MCP si aplicase
        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"

        # Guardamos el mensaje actual del usuario en la memoria global de la sesión
        HISTORIAL_MENSAJES_GLOBAL[session_id].append(
            types.Content(role="user", parts=[types.Part.from_text(text=mensaje_final)])
        )

        # Configuramos las instrucciones del sistema actualizadas dinámicamente con el estado real mutado
        config = types.GenerateContentConfig(
            system_instruction=f"{self.instruction}\n\n[SharedState Actual de la Memoria Backend]: {datos_cliente}",
            temperature=0.3 # Bajamos la temperatura para que sea más preciso y obedezca el contexto
        )

        # Invocamos el modelo generate_content enviándole TODO el historial unificado de la conversación
        # Esto garantiza que el nuevo agente conozca perfectamente lo que hablaste con los agentes anteriores
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

# 1. Agente Casual
subagente_casual = SubAgenteBaseConSesion(
    name="AgenteCasual",
    instruction=(
        "Eres un compañero de conversación amigable y casual. Mantén tus respuestas "
        "cortas, naturales y amables.\n"
        "Reglas: Responde en 3 oraciones o menos. NO inventes información técnica o comercial. "
        "Si detectas consultas del negocio solar, avisa que derivarás la charla."
    )
)

# 2. Agente Coloquial Solar
subagente_coloquial = SubAgenteBaseConSesion(
    name="AgenteColoquial",
    instruction=(
        "Eres un asesor de atención al cliente empático para una empresa de energía solar. "
        "Tu objetivo es guiar la charla de forma amena. Revisa con extrema atención el [SharedState]: "
        "si el cliente ya te dijo su nombre, su ciudad, su consumo o el tipo de sistema, "
        "NO se lo vuelvas a preguntar jamás. Avanza orgánicamente pidiéndole solo los datos que falten. "
        "Si ya completó todos los datos, felicítalo y dale el pase al equipo técnico o comercial de forma cordial."
    )
)

# 3. Agente Técnico
subagente_tecnico = SubAgenteBaseConSesion(
    name="AgenteTecnico",
    instruction=(
        "Eres un ingeniero especialista en dimensionamiento solar fotovoltaico. Responde dudas técnicas sobre paneles, "
        "inversores, espacio en techos e inclemencias climáticas. Usa obligatoriamente los datos "
        "del RAG técnico inyectados para fundamentar tus respuestas según la ley de generación distribuida. "
        "Jamás imprimas texto de depuración o diccionarios en tu respuesta."
    ),
    tools=[consultar_normativas_solares]
)

# 4. Agente Comercial
subagente_comercial = SubAgenteBaseConSesion(
    name="AgenteComercial",
    instruction=(
        "Eres el asesor financiero especialista en costos del equipo solar. Calculas presupuestos estimados y el retorno de inversión (ROI). "
        "Analiza el historial: el cliente ya te dio su consumo y su ciudad, no los pidas de nuevo. "
        "Responde directamente calculando el retorno de inversión (ROI), explicando qué significa y cuánto tardaría en recuperar la plata. "
        "Si el usuario confirma que desea avanzar o registrar sus datos, indícales que procederás a guardarlo en el CRM de la empresa."
    ),
    tools=[mcp_guardar_cliente_crm]
)


# =========================================================================
# AGENTE ORQUESTADOR CENTRAL (LÓGICA MULTIAGENTE Y ENRUTAMIENTO JERÁRQUICO)
# =========================================================================
class OrquestadorSolar:
    def __init__(self):
        self.name = "OrquestadorSolar"

    def route_request(self, user_input, datos_cliente):
        """
        Analiza la entrada del usuario, extrae datos estructurados en segundo plano y elige al subagente experto.
        """
        mensaje = user_input.lower()

        # BLOQUE A: Extractor JSON optimizado en segundo plano
        prompt_extractor = f"""
        Actúa como un extractor de entidades ultra preciso para un sistema de energía solar.
        Analiza el nuevo mensaje buscando menciones de nombre, ciudad, consumo o tipo de sistema.

        Estado de memoria actual: {datos_cliente} 
        Nuevo mensaje recibido: "{user_input}" 

        Devuelve UNICAMENTE un objeto JSON puro con las llaves: nombre, ciudad, consumo_anual_kwh, tipo_sistema.
        Si no hay datos nuevos para una llave, mantén el valor preexistente del Estado actual.
        Está prohibido agregar texto extra o marcas de código markdown.
        """
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            
            for k, v nuevos_datos.items():
                if v is not None:
                    datos_cliente[k] = v
        except Exception:
            pass 

        # BLOQUE B: LÓGICA DE ENRUTAMIENTO JERÁRQUICO MULTIAGENTE
        if any(word in mensaje for word in ["salir", "chau", "adios", "hasta luego", "terminar", "cerrar", "basta"]):
            return subagente_casual


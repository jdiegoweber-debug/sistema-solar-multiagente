import os # Manejo de variables de entorno y rutas del sistema operativo
import json # Codificación y decodificación de datos en formato estructurado JSON
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

# Regla global de localización para obligar a los modelos a usar lenguaje local
REGLA_ARGENTINA = (
    "\n\n[REGLA DE LOCALIZACIÓN OBLIGATORIA]: Debes hablar utilizando exclusivamente "
    "el dialecto castellano rioplatense (de Argentina). Trata al usuario de 'vos' (voseo). "
    "Está terminantemente prohibido usar modismos de España o México como 'vale', 'platicar', 'computadora', etc. "
    "Usa expresiones naturales de Argentina como 'dale', 'che', 'contame', 'factura de luz'."
)

# =========================================================================
# CLASE BASE PARA SUB-AGENTES CON MEMORIA DE SESIÓN INDEPENDIENTE
# =========================================================================
class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name 
        self.instruction = instruction + REGLA_ARGENTINA # Acoplamos la regla argentina a cada agente
        self.tools = tools or [] 
        self._sesiones = {} 

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default"):
        """
        Gestiona la conversación histórica del cliente e inyecta dinámicamente las herramientas RAG o MCP.
        """
        if session_id not in self._sesiones:
            config = types.GenerateContentConfig(
                system_instruction=f"{self.instruction}\n\n[SharedState - Memoria Actual del Cliente]: {datos_cliente}"
            )
            self._sesiones[session_id] = client.chats.create(model='gemini-2.5-flash', config=config)

        contexto_herramientas = ""
        
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas = f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
            
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas = f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"

        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"
        response = self._sesiones[session_id].send_message(mensaje_final)
        return response.text


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

# 2. Agente Coloquial Solar (Perfilador de clientes y recolector de los 4 datos clave)
subagente_coloquial = SubAgenteBaseConSesion(
    name="AgenteColoquial",
    instruction=(
        "Eres un asesor de atención al cliente empático para una empresa de energía solar. "
        "Tu objetivo es guiar la charla de forma amena. Revisa con extrema atención el [SharedState] "
        "y el historial del chat: si el cliente ya te dijo su nombre o su ciudad en algún turno, "
        "NO se lo vuelvas a preguntar jamás. Avanza orgánicamente pidiéndole los datos que falten "
        "(consumo eléctrico mensual/anual o tipo de sistema deseado)."
    )
)

# 3. Agente Técnico (Ingeniero fotovoltaico respaldado por RAG Vectorial)
subagente_tecnico = SubAgenteBaseConSesion(
    name="AgenteTecnico",
    instruction=(
        "Eres un ingeniero especialista en dimensionamiento solar fotovoltaico. Responde dudas técnicas sobre paneles, "
        "inversores, espacio en techos e inclemencias climáticas. Usa obligatoriamente los datos "
        "del RAG técnico inyectados para fundamentar tus respuestas según la ley de generación distribuida."
    ),
    tools=[consultar_normativas_solares]
)

# 4. Agente Comercial (Asesor financiero con persistencia CRM vía MCP)
subagente_comercial = SubAgenteBaseConSesion(
    name="AgenteComercial",
    instruction=(
        "Eres el asesor financiero del equipo solar. Calculas presupuestos estimados y el retorno de inversión (ROI). "
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

        # BLOQUE A: Extractor JSON optimizado para ser mucho más flexible y detectar datos cruzados
        prompt_extractor = f"""
        Actúa como un extractor de entidades ultra preciso para un sistema de energía solar.
        Analiza detalladamente el nuevo mensaje del usuario buscando menciones explícitas o implícitas de su nombre, 
        su ciudad geográfica, su consumo eléctrico o el tipo de sistema que prefiere.

        Estado de memoria actual: {datos_cliente} 
        Nuevo mensaje recibido: "{user_input}" 

        Instrucciones críticas de extracción:
        1. Si el usuario menciona un lugar geográfico (ej: "Tandil", "Mendoza", "Córdoba"), guárdalo en 'ciudad'.
        2. Si menciona su identidad (ej: "soy Diego Weber", "mi nombre es Juan"), guárdalo en 'nombre'.
        3. Mantén los datos preexistentes del Estado actual si el nuevo mensaje no los contradice.
        4. Devuelve UNICAMENTE un objeto JSON puro con las llaves: nombre, ciudad, consumo_anual_kwh, tipo_sistema.
        5. Si no hay datos nuevos para una llave, pon el valor que ya tenía el Estado actual (no pongas null si ya existía un dato).
        6. Está prohibido agregar texto extra, introducciones o marcas de código markdown.
        """
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            
            # Muta la memoria común compartida resguardando la información
            for k, v in nuevos_datos.items():
                if v is not None:
                    datos_cliente[k] = v
        except Exception:
            pass 

        # BLOQUE B: LÓGICA DE ENRUTAMIENTO JERÁRQUICO MULTIAGENTE
        
        # 1. Regla de Despedida
        if any(word in mensaje for word in ["salir", "chau", "adios", "hasta luego", "terminar", "cerrar", "basta"]):
            return subagente_casual

        # 2. Regla de Saludos o Charlas Informales
        if mensaje in ["hola", "buen dia", "buenas", "gracias"] or any(word in mensaje for word in ["chiste", "que haces", "hola cómo estás"]):
            if not datos_cliente.get("nombre") or not datos_cliente.get("ciudad"):
                return subagente_coloquial
            return subagente_casual

        # 3. Enrutamiento al Especialista Técnico (Disparadores RAG)
        if any(word in mensaje for word in ["panel", "techo", "bateria", "granizo", "ingenieria", "inversor", "ley", "medidor", "generacion", "distribuida"]):
            return subagente_tecnico

        # 4. Enrutamiento al Asesor Comercial (Disparadores MCP)
        if any(word in mensaje for word in ["precio", "costo", "financiar", "presupuesto", "roi", "plata", "guardar", "crm", "comprar"]):
            return subagente_comercial

        # Fallback por defecto si no encaja estrictamente en ninguna categoría
        return subagente_coloquial

solar_orchestrator = OrquestadorSolar()

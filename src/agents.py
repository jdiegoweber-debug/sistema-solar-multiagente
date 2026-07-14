import os # Manejo de variables de entorno y rutas del sistema operativo
import json # Codificación y decodificación de datos en formato estructurado JSON
from google import genai # El SDK moderno y oficial de Google para consumir modelos Gemini
from google.genai import types # Configuraciones tipadas avanzadas para los chats de la API
from dotenv import load_dotenv # Carga segura de claves de desarrollo desde el archivo .env

# =========================================================================
# IMPORTACIÓN DE HERRAMIENTAS TÉCNICAS Y COMERCIALES (PROTOCOLO RAG Y MCP)
# =========================================================================
# Cargamos tu motor de búsqueda semántica por similitud coseno basado en embeddings vectoriales o fallback local
from src.tools.rag_tool import consultar_normativas_solares
# Cargamos tu herramienta MCP simulada para persistir los leads interesados directamente en el CRM corporativo
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm

# Inicializamos las variables de entorno levantando tu clave privada GEMINI_API_KEY
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# =========================================================================
# CLASE BASE PARA SUB-AGENTES CON MEMORIA DE SESIÓN INDEPENDIENTE
# =========================================================================
class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name # Nombre identificatorio del agente experto (ej. AgenteTecnico)
        self.instruction = instruction # Pront del sistema o rol asignado por ingeniería de instrucciones
        self.tools = tools or [] # Listado de herramientas externas asociadas al especialista
        self._sesiones = {} # Diccionario interno en memoria para aislar los hilos de chat por cada cliente

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default"):
        """
        Gestiona la conversación histórica del cliente e inyecta dinámicamente las herramientas RAG o MCP.
        """
        # Inicializamos el chat histórico con su configuración de sistema si es el primer mensaje de la sesión
        if session_id not in self._sesiones:
            config = types.GenerateContentConfig(
                system_instruction=f"{self.instruction}\n\n[SharedState - Memoria Actual del Cliente]: {datos_cliente}"
            )
            # Creamos el objeto chat nativo de Gemini que mantiene automáticamente el contexto de turnos anteriores
            self._sesiones[session_id] = client.chats.create(model='gemini-2.5-flash', config=config)

        # Bloque de lógica integrada de ejecución de herramientas
        contexto_herramientas = ""
        
        # Inyección dinámica del RAG si el agente posee la herramienta y el usuario consulta temas técnicos
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas = f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
            
        # Inyección dinámica del protocolo MCP si el agente posee la herramienta y el usuario decide registrarse
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas = f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"

        # Ensamblamos el mensaje final sumando el aporte del RAG o MCP si aplicase
        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"
        
        # Despachamos el mensaje final al hilo histórico de Gemini
        response = self._sesiones[session_id].send_message(mensaje_final)
        
        # Retornamos el texto plano generado por el modelo
        return response.text


# =========================================================================
# INSTANCIAS DE SUB-AGENTES ESPECIALIZADOS
# =========================================================================

# 1. Agente Casual (Filtro conversacional básico para saludos o bromas)
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
        "Tu objetivo es guiar la charla de forma amena. Intenta averiguar sutilmente el nombre, "
        "ciudad, consumo eléctrico y tipo de sistema del cliente si faltan en la memoria compartida, lo ideal es que le des un pantallazo al cliente de todos los datos que vas a necesitar pero que despues le vallas preguntand las cosas de a una y dando opciones, sino el cliente se marea con tanta informacion junta."
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

        # BLOQUE A: Extractor JSON en segundo plano para actualizar el SharedState de forma dinámica
        prompt_extractor = f"""
        Analiza el mensaje del usuario y extrae datos relevantes. 
        Estado actual: {datos_cliente} 
        Nuevo mensaje: "{user_input}" 
        Devuelve un objeto JSON con las llaves: nombre, ciudad, consumo_anual_kwh, tipo_sistema. 
        Si no detectas cambios pon null. No agregues texto extra, marcas markdown ni introducciones.
        """
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            # Muta la memoria común compartida con los datos frescos capturados
            for k, v in nuevos_datos.items():
                if v is not None:
                    datos_cliente[k] = v
        except Exception:
            pass # Si el parseo falla, el sistema continúa el flujo de forma silenciosa para no interrumpir la experiencia

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

# Creamos la instancia global exacta requerida por tu archivo src/main.py
solar_orchestrator = OrquestadorSolar()

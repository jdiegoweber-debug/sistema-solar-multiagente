import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importación de Herramientas Locales
from src.tools.rag_tool import consultar_normativas_solares
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name
        self.instruction = instruction
        self.tools = tools or []
        # Diccionario para gestionar hilos de chat independientes por sesión
        self._sesiones = {}

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default"):
        # Inicializa el chat histórico si es el primer mensaje de la sesión
        if session_id not in self._sesiones:
            config = types.GenerateContentConfig(
                system_instruction=f"{self.instruction}\n\n[SharedState - Memoria Actual del Cliente]: {datos_cliente}"
            )
            self._sesiones[session_id] = client.chats.create(model='gemini-2.5-flash', config=config)

        # Lógica integrada de ejecución de herramientas para inyectar al contexto del chat
        contexto_herramientas = ""
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas = f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
            
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas = f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"

        # Enviamos el mensaje al objeto chat, el cual guarda la memoria de turnos automáticamente
        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"
        response = self._sesiones[session_id].send_message(mensaje_final)
        return response.text

# ==========================================
# INSTANCIAS DE SUB-AGENTES ESPECIALIZADOS
# ==========================================

# 1. Agente Casual (Filtro de charlas informales - Traducido y adaptado)
subagente_casual = SubAgenteBaseConSesion(
    name="AgenteCasual",
    instruction=(
        "Eres un compañero de conversación amigable y casual. Mantén tus respuestas "
        "cortas, naturales y amables.\n\n"
        "Ejemplos de lo que manejas:\n"
        '- "Hola, ¿cómo estás?" — Saluda cordialmente.\n'
        '- "¡Muchas gracias!" — Agradece educadamente.\n'
        '- "Contame un chiste." — Comparte un chiste corto y limpio.\n'
        '- "¿Qué podés hacer?" — Explica brevemente que eres un asistente inicial.\n\n'
        "Reglas:\n"
        "- Responde en 3 oraciones o menos.\n"
        "- NO inventes información técnica, legal, médica o comercial.\n"
        "- Si la pregunta requiere datos externos, herramientas, conocimiento técnico o "
        "experiencia en energía solar, indica que transferirás la consulta al especialista."
    )
)

# 2. Agente Coloquial Solar (Recolección de perfil del cliente)
subagente_coloquial = SubAgenteBaseConSesion(
    name="AgenteColoquial",
    instruction=(
        "Eres un asesor de atención al cliente empático y amigable para una empresa de energía solar. "
        "Tu objetivo es guiar la charla. Revisa el historial del chat: si ya saludaste al usuario o te presentaste, "
        "NO vuelvas a hacerlo, continúa la conversación de forma orgánica. Intenta averiguar sutilmente su nombre, "
        "ciudad y consumo eléctrico si es que faltan en la memoria."
    )
)

# 3. Agente Técnico (Ingeniería y RAG)
subagente_tecnico = SubAgenteBaseConSesion(
    name="AgenteTecnico",
    instruction=(
        "Eres un ingeniero especialista en dimensionamiento solar fotovoltaico. Responde dudas técnicas sobre paneles, "
        "inversores, espacio en techos e inclemencias climáticas (como el granizo). Usa obligatoriamente los datos "
        "del RAG técnico inyectados para fundamentar tus respuestas según la ley de generación distribuida."
    ),
    tools=[consultar_normativas_solares]
)

# 4. Agente Comercial (Costos y MCP CRM)
subagente_comercial = SubAgenteBaseConSesion(
    name="AgenteComercial",
    instruction=(
        "Eres el asesor financiero del equipo solar. Calculas presupuestos estimados y el retorno de inversión (ROI). "
        "Si el usuario confirma que desea avanzar o registrar sus datos, indícales que procederás a guardarlo en el CRM de la empresa."
    ),
    tools=[mcp_guardar_cliente_crm]
)

# ==========================================
# AGENTE ORQUESTADOR (LÓGICA MULTIAGENTE)
# ==========================================

class OrquestadorSolar:
    def __init__(self):
        self.name = "OrquestadorSolar"

    def route_request(self, user_input, datos_cliente):
        mensaje = user_input.lower()
        
        # Extractor JSON en segundo plano para actualizar el SharedState dinámicamente
        prompt_extractor = f"""
        Analiza el mensaje del usuario y extrae datos relevantes.
        Estado actual: {datos_cliente}
        Nuevo mensaje: "{user_input}"
        Devuelve un objeto JSON con las llaves: nombre, ciudad, consumo_anual_kwh, tipo_sistema. Si no detectas cambios pon null. No agregues texto extra.
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

               # --- LÓGICA DE ENRUTAMIENTO JERÁRQUICO MULTIAGENTE ---
        
        # 1. REGLA DE SALIDA/DESPEDIDA: Si el cliente quiere cortar, usamos el AgenteCasual
        # Este agente tiene la regla de responder en menos de 3 oraciones y no repreguntar.
        if any(word in mensaje for word in ["salir", "chau", "adios", "hasta luego", "hasta la proxima", "terminar", "cerrar", "basta"]):
            return subagente_casual

        # 2. Si es un saludo inicial o charla genérica, va al Casual también
        if mensaje in ["hola", "buen dia", "buenas", "gracias"] or any(word in mensaje for word in ["chiste", "que haces", "hola cómo estás"]):
            if not datos_cliente.get("nombre") or not datos_cliente.get("ciudad"):
                return subagente_coloquial
            return subagente_casual
            
        # 3. Consultas de ingeniería y normativas van al Técnico (RAG)
        if any(word in mensaje for word in ["panel", "techo", "bateria", "granizo", "ingenieria", "inversor", "ley", "medidor", "generacion", "distribuida"]):
            return subagente_tecnico
            
        # 4. Consultas de costos, presupuestos o persistencia van al Comercial (MCP)
        if any(word in mensaje for word in ["precio", "costo", "financiar", "presupuesto", "roi", "plata", "guardar", "crm", "comprar"]):
            return subagente_comercial
            
        # Fallback por defecto al asesor coloquial
        return subagente_coloquial


solar_orchestrator = OrquestadorSolar()

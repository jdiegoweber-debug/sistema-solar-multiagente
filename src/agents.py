import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- IMPORTACIÓN DE HERRAMIENTAS ---
from src.tools.rag_tool import consultar_normativas_solares
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class SubAgenteBaseConSesion:
    """Clase base para subagentes con gestión de memoria y herramientas."""
    def __init__(self, name, instruction, tools=None):
        self.name = name
        self.instruction = instruction
        self.tools = tools or []
        self._sesiones = {}

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default"):
        if session_id not in self._sesiones:
            config = types.GenerateContentConfig(
                system_instruction=f"{self.instruction}\n\n[SharedState]: {datos_cliente}"
            )
            self._sesiones[session_id] = client.chats.create(model='gemini-2.5-flash', config=config)

        contexto_herramientas = ""
        
        # --- LÓGICA DE HERRAMIENTAS (RAG/MCP) ---
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "ley"]):
            contexto_herramientas = f"\n\n[RAG]: {consultar_normativas_solares(mensaje_usuario)}"
        
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm"]):
            contexto_herramientas = f"\n\n[MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''))}"

        response = self._sesiones[session_id].send_message(f"{mensaje_usuario}{contexto_herramientas}")
        return response.text

# --- INSTANCIAS DE SUB-AGENTES (CONSIGNA MULTIAGENTE) ---
subagente_casual = SubAgenteBaseConSesion(name="AgenteCasual", instruction="Compañero amigable, respuestas cortas.")
subagente_coloquial = SubAgenteBaseConSesion(name="AgenteColoquial", instruction="Asesor empático, recolecta nombre/ciudad/consumo.")
subagente_tecnico = SubAgenteBaseConSesion(name="AgenteTecnico", instruction="Ingeniero solar, usa RAG.", tools=[consultar_normativas_solares])
subagente_comercial = SubAgenteBaseConSesion(name="AgenteComercial", instruction="Asesor financiero, usa MCP.", tools=[mcp_guardar_cliente_crm])

class OrquestadorSolar:
    """Supervisor de flujo y extractor de entidades."""
    def __init__(self):
        self.name = "OrquestadorSolar"

    def route_request(self, user_input, datos_cliente):
        mensaje = user_input.lower()
        
        # --- EXTRACTOR DE ENTIDADES (JSON) ---
        prompt_extractor = f"Analiza: '{user_input}'. Estado: {datos_cliente}. JSON: nombre, ciudad, consumo, tipo."
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            nuevos_datos = json.loads(res.text.strip().replace("```json", "").replace("```", ""))
            for k, v in nuevos_datos.items():
                if v: datos_cliente[k] = v
        except: pass

        # --- ENRUTAMIENTO ---
        if any(w in mensaje for w in ["salir", "chau"]): return subagente_casual
        if any(w in mensaje for w in ["panel", "techo", "ley"]): return subagente_tecnico
        if any(w in mensaje for w in ["precio", "guardar"]): return subagente_comercial
        return subagente_coloquial

solar_orchestrator = OrquestadorSolar()

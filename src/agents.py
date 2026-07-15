# src/agents.py
import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pypdf import PdfReader

from src.tools.web_reader_tool import leer_contenido_enlace_web
from src.tools.mcp_crm_tool import mcp_guardar_cliente_crm
from src.tools.rag_tool import consultar_normativas_solares

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

REGLA_ARGENTINA = (
    "\n\n[REGLA DE LOCALIZACIÓN OBLIGATORIA]: Debes hablar utilizando exclusivamente el dialecto castellano rioplatense (de Argentina). Trata al usuario de 'vos' (voseo). Está terminantemente prohibido usar modismos de España o México. Usa expresiones naturales de Argentina como 'dale', 'che', 'contame'."
    "\n\n[REGLA DE PRIVACIDAD]: Tienes acceso a 'SharedState'. Está TERMINANTEMENTE PROHIBIDO volver a preguntar datos que ya figuren allí. No escribas el texto '[SharedState]' en tu respuesta."
)

HISTORIAL_MENSAJES_GLOBAL = {}

def obtener_contexto_pdf_local(consulta_usuario: str) -> str:
    ruta_pdf = os.path.join("knowledge", "manual_solar.pdf")
    if not os.path.exists(ruta_pdf):
        return ""
    try:
        lector = PdfReader(ruta_pdf)
        fragmentos_utiles = []
        palabras_clave = [w.lower() for w in consulta_usuario.split() if len(w) > 3]
        for num_pag, pagina in enumerate(lector.pages, start=1):
            texto_pagina = pagina.extract_text()
            if any(pc in texto_pagina.lower() for pc in palabras_clave) or len(palabras_clave) == 0:
                fragmentos_utiles.append(f"[Manual PDF - Pág {num_pag}]: {texto_pagina[:1000]}...")
                if len(fragmentos_utiles) >= 2:
                    break
        if fragmentos_utiles:
            return "\n\n[INFORMACIÓN DE RESPALDO DETECTADA EN TU MANUAL PDF]:\n" + "\n".join(fragmentos_utiles)
        return ""
    except Exception:
        return ""

class SubAgenteBaseConSesion:
    def __init__(self, name, instruction, tools=None):
        self.name = name 
        self.instruction = instruction + REGLA_ARGENTINA 
        self.tools = tools or [] 

    def responder(self, mensaje_usuario, datos_cliente, session_id="consola_default", ruta_archivo=None):
        global HISTORIAL_MENSAJES_GLOBAL
        if session_id not in HISTORIAL_MENSAJES_GLOBAL:
            HISTORIAL_MENSAJES_GLOBAL[session_id] = []
        contexto_herramientas = ""
        contexto_pdf = obtener_contexto_pdf_local(mensaje_usuario)
        if contexto_pdf:
            contexto_herramientas += f"\n{contexto_pdf}"
        if consultar_normativas_solares in self.tools and any(w in mensaje_usuario.lower() for w in ["granizo", "bateria", "red", "ley", "medidor"]):
            contexto_herramientas += f"\n\n[Inyección RAG del Sistema]: {consultar_normativas_solares(mensaje_usuario)}"
        if mcp_guardar_cliente_crm in self.tools and any(w in mensaje_usuario.lower() for w in ["guardar", "crm", "registrar"]):
            contexto_herramientas += f"\n\n[Inyección Protocolo MCP]: {mcp_guardar_cliente_crm(datos_cliente.get('nombre',''), datos_cliente.get('ciudad',''), datos_cliente.get('consumo_anual_kwh',''), datos_cliente.get('tipo_sistema',''))}"
        if leer_contenido_enlace_web in self.tools and ("http://" in mensaje_usuario or "https://" in mensaje_usuario):
            urls = re.findall(r'(https?://[^\s]+)', mensaje_usuario)
            if urls:
                contexto_herramientas += f"\n\n[Contenido de la Factura Extraído de la Web]: {leer_contenido_enlace_web(urls)}"
        partes_mensaje = []
        if ruta_archivo and os.path.exists(ruta_archivo):
            try:
                print(f"📁 [File Service Cloud] Subiendo '{os.path.basename(ruta_archivo)}'...")
                archivo_google = client.files.upload(file=ruta_archivo)
                partes_mensaje.append(archivo_google)
            except Exception as e:
                contexto_herramientas += f"\n\n[Aviso del Sistema]: Error al cargar archivo: {e}"
        mensaje_final = f"{mensaje_usuario}{contexto_herramientas}"
        partes_mensaje.append(types.Part.from_text(text=mensaje_final))
        HISTORIAL_MENSAJES_GLOBAL[session_id].append(types.Content(role="user", parts=partes_mensaje))
        config = types.GenerateContentConfig(system_instruction=f"{self.instruction}\n\n[SharedState]: {datos_cliente}", temperature=0.3)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=HISTORIAL_MENSAJES_GLOBAL[session_id], config=config)
        respuesta_final = response.text
        HISTORIAL_MENSAJES_GLOBAL[session_id].append(types.Content(role="model", parts=[types.Part.from_text(text=respuesta_final)]))
        return respuesta_final

# --- INSTANCIAS EN UNA SOLA LÍNEA (EVITA ERRORES DE SINTAXIS) ---
subagente_casual = SubAgenteBaseConSesion("AgenteCasual", "Eres un compañero de conversación casual. Responde en 3 oraciones o menos. NO des datos técnicos.")
subagente_coloquial = SubAgenteBaseConSesion("AgenteColoquial", "Eres un asesor empático residencial. Averigua sutilmente datos del SharedState sin repetir. Revisa coherencia de consumo.")
subagente_tecnico = SubAgenteBaseConSesion("AgenteTecnico", "Eres un ingeniero fotovoltaico. Responde dudas técnicas basándote en el RAG y el manual PDF provisto.", tools=[consultar_normativas_solares])
subagente_comercial = SubAgenteBaseConSesion("AgenteComercial", "Eres el asesor financiero especialista en costos del equipo solar. Calculas presupuestos estimados y el retorno de inversión (ROI). Usa los números reales de la factura para ajustar el cálculo.", tools=[mcp_guardar_cliente_crm, leer_contenido_enlace_web])

class OrquestadorSolar:
    def __init__(self):
        self.name = "OrquestadorSolar"
    def _extraer_datos_bg(self, user_input, datos_cliente):
        prompt_extractor = f"Extrae datos (nombre, ciudad, consumo_anual_kwh, tipo_sistema) en JSON puro. Estado: {datos_cliente}. Mensaje: '{user_input}'"
        try:
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            for k, v in nuevos_datos.items():
                if v is not None: datos_cliente[k] = v
        except Exception: pass
    def route_request(self, user_input, datos_cliente):
        self._extraer_datos_bg(user_input, datos_cliente)
        mensaje = user_input.lower()
        if any(word in mensaje for word in ["salir", "chau", "adios", "hasta luego"]): return subagente_casual
        if any(word in mensaje for word in ["precio", "costo", "presupuesto", "roi", "plata", "guardar", "crm", "factura", "boleta", "pdf"]): return subagente_comercial
        if any(word in mensaje for word in ["medidor", "on grid", "off grid", "provincia", "capital", "normativa", "ley", "paneles", "bateria"]): return subagente_tecnico
        return subagente_coloquial

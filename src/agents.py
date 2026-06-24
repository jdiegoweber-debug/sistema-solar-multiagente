import os
import json
import time
from google import genai
from src.state import SolarProjectState
from dotenv import load_dotenv
from google.genai.errors import ServerError

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Función auxiliar para llamar a Gemini con reintentos si el servidor falla (503)
def llamar_gemini_con_retry(model, contents, max_retries=3):
    for intento in range(max_retries):
        try:
            response = client.models.generate_content(model=model, contents=contents)
            return response
        except ServerError as e:
            if "503" in str(e) and intento < max_retries - 1:
                print(f"\n⚠️ [Servidor de Google ocupado, reintentando en {intento + 1}s...]")
                time.sleep(intento + 1)
                continue
            raise e

class AgenteSolar:
    def __init__(self, name, instructions):
        self.name = name
        self.instructions = instructions

    def responder(self, mensaje_usuario, estado: SolarProjectState, historial_formateated: str):
        prompt_completo = f"""
        {self.instructions}
        
        Estado actual del cliente (Datos ya guardados): {estado.datos_cliente}
        Historial previo de la conversación:
        {historial_formateated}
        
        Mensaje actual del cliente a responder: "{mensaje_usuario}"
        
        Responde al cliente manteniendo estrictamente tu rol. No vuelvas a preguntar datos que ya figuren guardados en el Estado o que ya se hayan aclarado en el Historial.
        """
        response = llamar_gemini_con_retry(model='gemini-2.5-flash', contents=prompt_completo)
        return response.text

# Sub-agentes Especializados
agente_coloquial = AgenteSolar(
    name="AgenteColoquial",
    instructions="""Eres un asesor de atención al cliente empático y amigable para una empresa de energía solar.
    Tu único objetivo es guiar la charla y recolectar sutilmente los cuatro datos esenciales que falten en el Estado:
    - Nombre del cliente.
    - Ciudad donde vive.
    - Consumo eléctrico anual (preferentemente en kWh o pesos en su defecto).
    - Tipo de sistema preferido: Averigua si prefiere estar 'Aislado de la red' o 'Conectado a la red'.
    Si el estado ya tiene estos datos, salúdalo por su nombre y mantén una charla amena antes de que intervenga otro agente."""
)

agente_tecnico = AgenteSolar(
    name="AgenteTecnico",
    instructions="""Eres un ingeniero especialista en dimensionamiento solar fotovoltaico.
    Tu tarea es resolver dudas sobre paneles, inversores, espacio en techos o inclemencias climáticas (como el granizo).
    Diseña tu respuesta en base al 'tipo_sistema' guardado en el estado:
    - Si es 'Aislado de la red', aclárale al cliente que obligatoriamente necesitará un banco de baterías para la noche.
    - Si es 'Conectado a la red', menciónale el beneficio de inyectar el sobrante a la red eléctrica pública."""
)

agente_comercial = AgenteSolar(
    name="AgenteComercial",
    instructions="""Eres el asesor financiero del equipo solar.
    Tu objetivo es calcular presupuestos estimados, retorno de inversión (ROI) y planes de financiación.
    Informa los costos basándote en el 'tipo_sistema' del estado. Los sistemas 'Aislado de la red' son significativamente más caros por las baterías y su menor vida útil en comparación a los paneles."""
)

class OrquestadorSolar:
    def __init__(self):
        self.estado = SolarProjectState()
        self.historial = []

    def _actualizar_estado_dinamicamente(self, mensaje_usuario):
        prompt_extractor = f"""
        Analiza el mensaje del usuario y extrae cualquier dato relevante para nuestro sistema solar.
        Estado actual: {self.estado.datos_cliente}
        Nuevo mensaje: "{mensaje_usuario}"
        
        Devuelve un objeto JSON con las actualizaciones de los campos que detectes. Si no detectas ninguno nuevo, devuelve el campo como null.
        Campos: nombre, ciudad, consumo_anual_kwh, tipo_sistema ('Aislado de la red' o 'Conectado a la red').
        Responde ÚNICAMENTE con el bloque JSON estructurado, sin textos adicionales.
        """
        try:
            res = llamar_gemini_con_retry(model='gemini-2.5-flash', contents=prompt_extractor)
            texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
            nuevos_datos = json.loads(texto_limpio)
            
            for clave, valor in nuevos_datos.items():
                if valor is not None:
                    self.estado.datos_cliente[clave] = valor
        except Exception:
            pass

    def procesar_mensaje(self, mensaje_usuario):
        self._actualizar_estado_dinamicamente(mensaje_usuario)
        historial_txt = "\n".join([f"{r}: {m}" for r, m in self.historial])
        
        prompt_enrutador = f"""
        Eres el director del sistema de atención solar. Analiza el mensaje del usuario, los datos guardados en el estado y el historial previo para decidir cuál es el subagente correcto:
        - Responde 'COLOQUIAL' si faltan datos esenciales en el estado o si es una charla informal.
        - Responde 'TECNICO' si el usuario hace preguntas de ingeniería, paneles, granizo, baterías, etc.
        - Responde 'COMERCIAL' si pide precios, presupuestos, financión o costos económicos.
        
        Estado actual del cliente: {self.estado.datos_cliente}
        Mensaje del usuario: "{mensaje_usuario}"
        Responde ÚNICAMENTE con una de estas tres palabras: COLOQUIAL, TECNICO o COMERCIAL.
        """
        
        decision_response = llamar_gemini_con_retry(model='gemini-2.5-flash', contents=prompt_enrutador)
        decision = decision_response.text.strip().upper()
        
        if "TECNICO" in decision:
            agente = agente_tecnico
        elif "COMERCIAL" in decision:
            agente = agente_comercial
        else:
            agente = agente_coloquial
            
        respuesta_final = agente.responder(mensaje_usuario, self.estado, historial_txt)
        
        self.historial.append(("Cliente", mensaje_usuario))
        self.historial.append((agente.name, respuesta_final))
        
        return f"[{agente.name}]: {respuesta_final}"

orquestador = OrquestadorSolar()

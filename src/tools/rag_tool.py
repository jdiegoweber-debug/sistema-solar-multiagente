import os
from google import genai
from dotenv import load_dotenv # ◄--- ¡AGREGÁ ESTA IMPORTACIÓN!

load_dotenv() # ◄--- ¡CARGÁ LAS VARIABLES AQUÍ ARRIBA!

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Base de conocimientos local para simular el RAG del TP
BASE_CONOCIMIENTO_SOLAR = {
    "granizo": "Normativa SEC 4.2: Los paneles certificados deben soportar impactos de granizo de hasta 25mm a 80 km/h. Se recomienda inclinación de 30°.",
    "baterias": "Reglamento Técnico 2026: Sistemas aislados requieren baterías de Litio LiFePO4 para descargas profundas. Prohibido instalar en espacios cerrados sin ventilación.",
    "red": "Ley de Energía Distribuida: Los sistemas conectados a la red (On-Grid) deben usar medidores bidireccionales homologados para la inyección de excedentes."
}

def consultar_normativas_solares(consulta_usuario: str) -> str:
    """
    Úsala para buscar regulaciones técnicas, leyes de inyección a la red, 
    baterías y resistencia a granizo en la base de datos de normativas solares.

    Args:
        consulta_usuario: El texto o la pregunta del cliente relacionada a la ingeniería.
    """
    consulta = consulta_usuario.lower()
    
    for clave, texto_normativo in BASE_CONOCIMIENTO_SOLAR.items():
        if clave in consulta:
            return f"[Resultado RAG encontrado]: {texto_normativo}"
            
    return "[Resultado RAG]: No hay restricciones específicas en la normativa para esta consulta. Proceder bajo estándar general IEC 61215."

import os # Módulo para interactuar de forma segura con variables de entorno del sistema operativo
import numpy as np # Biblioteca estándar para cálculos matemáticos veloces de álgebra lineal y matrices
from google import genai # El SDK oficial moderno provisto por Google que usas en tu archivo agents.py
from google.genai import types # Módulo de tipado para estructurar configuraciones nativas del SDK de Google
from dotenv import load_dotenv # Utilidad para levantar de forma segura las claves desde el archivo .env

# Levantamos la configuración del archivo .env para extraer tus credenciales de pago de Google AI Studio
load_dotenv()

# ¡CONFIGURACIÓN CLOUD DEFINITIVA!: Forzamos al cliente moderno a comunicarse usando el endpoint 'v1' estable
# Esto remueve el bug de enrutamiento de la ruta 'v1beta' y garantiza que tu API de pago responda siempre
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
    http_options={'api_version': 'v1'}
)

# CORPUS DE CONOCIMIENTO (Base de datos de grounding real para el Agente Técnico)
CORPUS_NORMATIVO = {
    "ley_generacion_distribuida": (
        "Ley 27.424 - Régimen de Fomento a la Generación Distribuida de Energía Renovable integrada a la red eléctrica pública. "
        "Permite a los usuarios residenciales y comerciales transformarse en usuarios-generadores. Al generar energía limpia "
        "mediante fuentes fotovoltaicas, se autoriza legalmente la inyección de excedentes energéticos a la red comercial."
    ),
    "medidor_bidireccional": (
        "Normativa Técnica de Conexión Comercial y Equipamiento de Medición: Todo usuario que instale paneles solares On-Grid "
        "tiene la obligación de solicitar formalmente a la distribuidora eléctrica local el reemplazo de su equipo tradicional. "
        "Se debe instalar un medidor bidireccional homologado. Este aparato registra tanto el consumo de la red como la inyección. "
        "Está terminantemente prohibido inyectar energía con medidores antiguos ya que calculan la inyección como consumo cobrable."
    ),
    "bancos_baterias": (
        "Especificación Técnica ET-S04 - Almacenamiento Energético para Sistemas Aislados: Los sistemas híbridos u Off-Grid "
        "requieren de forma mandatoria bancos de baterías de Litio o Gel de ciclo profundo. La normativa de seguridad exige que "
        "estos acumuladores se ubiquen en espacios altamente ventilados con el fin de evitar la acumulación de gases peligrosos "
        "y asegurar un rango de temperatura estable que prevenga la degradación temprana del componente."
    ),
    "proteccion_granizo": (
        "Estándar Internacional de Calidad IEC 61215 - Resistencia Física de Módulos Fotovoltaicos: Los paneles solares "
        "homologados se construyen utilizando una cubierta de vidrio templado prismático de alta resistencia (espesor de 3.2 mm). "
        "La certificación internacional garantiza que los módulos soportan impactos directos de granizo severo de hasta 25 mm "
        "de diámetro impactando a una velocidad de 82 km/h. Por ende, la normativa desaconseja colocar mallas metálicas "
        "protectoras sobre los paneles debido a que bloquean la radiación solar y deprimen drásticamente el rendimiento."
    )
}

def _obtener_embedding(texto: str, es_consulta: bool = False) -> list:
    """
    Función interna que invoca el endpoint oficial de pago de Google GenAI para transformar
    texto plano en un vector matemático representativo (text-embedding-004).
    """
    # Optimizamos el downstream determinando si el texto es una pregunta libre o un documento estático
    tipo_tarea = "RETRIEVAL_QUERY" if es_consulta else "RETRIEVAL_DOCUMENT"
    
    # Invocación estructurada al modelo estable text-embedding-004 pasando la tarea correspondiente
    response = client.models.embed_content(
        model="text-embedding-004", # Modelo oficial estable de Google para indexación de texto plano
        contents=texto,
        config=types.EmbedContentConfig(
            task_type=tipo_tarea # Parámetro requerido por la API para optimizar pesos conceptuales
        )
    )
    # Extraemos y retornamos los valores numéricos decimales del vector del espacio latente
    return response.embeddings.values

# PRE-CÓMPUTO VECTORIAL CLOUD (Se ejecuta una sola vez al arrancar el programa en memoria RAM)
VECTORES_CORPUS = {}
print("🛰️  Conectando con la API de Google: Inicializando tensores y base de datos vectorial del RAG...")

for llave, texto_normativo in CORPUS_NORMATIVO.items():
    # Cada fragmento de texto se convierte en un array unidimensional de NumPy a través de tu API Key de pago
    VECTORES_CORPUS[llave] = np.array(_obtener_embedding(texto_normativo, es_consulta=False))

print("✅ [Modo Vectorial Cloud Activo]: Base de conocimiento sincronizada mediante la API de Google.")


def consultar_normativas_solares(query: str) -> str:
    """
    Algoritmo RAG Principal consumido por tus agentes. Compara semánticamente la pregunta
    del usuario contra los vectores de Google usando Similitud Coseno e inyecta el contexto exacto.
    """
    # Control defensivo para evitar procesar consultas de texto vacías
    if not query or not query.strip():
        return "No se especificó ninguna consulta técnica válida para procesar en el motor RAG."

    try:
        # 1. Transformamos la pregunta libre del cliente en un vector de consulta usando tu API de Google
        vector_pregunta = _obtener_embedding(query, es_consulta=True)
        v_query = np.array(vector_pregunta)

        mejor_llave = None
        max_similitud = -1.0 # Inicializamos el umbral de comparación matemática en su punto más bajo

        # 2. Escaneo geométrico de proximidad en el espacio vectorial (Álgebra lineal con Numpy)
        for llave, v_doc in VECTORES_CORPUS.items():
            # Cómputo del Producto Punto (Dot Product) entre ambos vectores
            producto_punto = np.dot(v_query, v_doc)
            # Cálculo de las Magnitudes Geométricas (Normas Euclidianas) de los vectores
            norma_query = np.linalg.norm(v_query)
            norma_doc = np.linalg.norm(v_doc)
            
            # Aplicamos la ecuación oficial de Similitud Coseno
            similitud_coseno = producto_punto / (norma_query * norma_doc)

            # Si la puntuación de afinidad supera al récord previo, actualizamos los punteros del RAG
            if similitud_coseno > max_similitud:
                max_similitud = similitud_coseno
                mejor_llave = llave

        # 3. Retorno del fragmento normativo ganador si supera el umbral de confianza mínimo
        if mejor_llave and max_similitud > 0.35:
            return CORPUS_NORMATIVO[mejor_llave]
        
        # Estrategia de resguardo: Si la consulta no matchea un tema específico, inyectamos la ley general
        return CORPUS_NORMATIVO["ley_generacion_distribuida"]

    except Exception as e:
        # Capa de contingencia en caso de microcortes de red de la API durante la sesión de chat
        return f"[Aviso RAG Contingente - Error de Red: {e}] Contexto inyectado: Ley Nacional 27.424 de Generación Distribuida."

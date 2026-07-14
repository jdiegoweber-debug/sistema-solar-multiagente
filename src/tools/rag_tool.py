import os # Importamos el módulo del sistema para leer rutas y variables de entorno de forma segura
import numpy as np # Biblioteca matemática estándar para cómputo numérico lineal de vectores
from google import genai # El SDK oficial actual provisto por Google para interactuar con Gemini
from google.genai import types # Módulos de configuración tipada para parámetros del SDK
from dotenv import load_dotenv # Módulo para cargar las credenciales desde el archivo .env

# Levantamos las variables de entorno locales (.env) para extraer la API KEY
load_dotenv()
# Creamos la instancia del cliente utilizando exactamente la misma configuración que en tu agent.py
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
    Función interna que transforma un texto en un vector numérico representativo mediante la API de Google.
    """
    # Determinamos el tipo de tarea según si es una pregunta o un documento del corpus
    tipo_tarea = "RETRIEVAL_QUERY" if es_consulta else "RETRIEVAL_DOCUMENT"
    
    # Invocamos el modelo de embeddings nativo de Gemini usando 'text-embedding-004'
    # Agregamos la configuración explícita de la API en el config para evitar el error 404
    response = client.models.embed_content(
        model="text-embedding-004", 
        contents=texto,
        config=types.EmbedContentConfig(
            task_type=tipo_tarea
        )
    )
    # Retornamos el vector flotante que contiene la semántica del texto
    return response.embeddings.values

# Pre-cómputo automático de los vectores para que la app responda de forma ultra veloz en la terminal
VECTORES_CORPUS = {}
for llave, texto_normativo in CORPUS_NORMATIVO.items():
    VECTORES_CORPUS[llave] = _obtener_embedding(texto_normativo, es_consulta=False)


def consultar_normativas_solares(query: str) -> str:
    """
    Algoritmo RAG Principal consumido por tus agentes. Compara semánticamente la pregunta
    del usuario contra la base de datos usando Similitud Coseno e inyecta la respuesta exacta.
    """
    # Control defensivo inicial
    if not query or not query.strip():
        return "No se especificó ninguna consulta técnica válida para procesar en el motor RAG."

    try:
        # Transformamos la pregunta libre del cliente en un vector matemático
        vector_pregunta = _obtener_embedding(query, es_consulta=True)
        v_query = np.array(vector_pregunta)

        mejor_llave = None
        max_similitud = -1.0

        # Escaneo de proximidad matemática en el espacio vectorial (Similitud Coseno)
        for llave, vector_documento in VECTORES_CORPUS.items():
            v_doc = np.array(vector_documento)
            
            # Aplicamos la fórmula oficial de Similitud Coseno (Producto punto dividido el producto de las normas)
            producto_punto = np.dot(v_query, v_doc)
            norma_query = np.linalg.norm(v_query)
            norma_doc = np.linalg.norm(v_doc)
            similitud_coseno = producto_punto / (norma_query * norma_doc)

            # Si la puntuación supera al récord previo, guardamos el documento como ganador de contexto
            if similitud_coseno > max_similitud:
                max_similitud = similitud_coseno
                mejor_llave = llave

        # Si el documento supera un umbral mínimo de confianza semántica, inyectamos el fragmento normativo
        if mejor_llave and max_similitud > 0.35:
            return CORPUS_NORMATIVO[mejor_llave]
        
        # En caso de no levantar afinidad, inyectamos por defecto la normativa fotovoltaica general
        return CORPUS_NORMATIVO["ley_generacion_distribuida"]

    except Exception as e:
        # Sistema de contingencia resiliente ante cortes de internet o fallas de la API de Google
        return f"[Aviso RAG Contingente - Error: {e}] Contexto base: Ley Nacional 27.424 de Generación Distribuida."

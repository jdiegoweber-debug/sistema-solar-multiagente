import os
import numpy as np # Biblioteca matemática estándar para cálculo numérico y operaciones con vectores
from google import genai # El SDK oficial y moderno provisto por Google que usas en tu proyecto
from dotenv import load_dotenv # Módulo para extraer de forma segura variables de entorno locales

# 1. CARGA DE CONFIGURACIÓN E INICIALIZACIÓN DEL CLIENTE DE IA
load_dotenv() # Lee el archivo .env de la raíz para disponibilizar las credenciales del sistema
# Creamos la instancia reutilizando la API KEY del entorno, exactamente igual que hacés en agent.py
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 2. BASE DE CONOCIMIENTO (CORPUS INTEGRADO DE LA LEY DE GENERACIÓN DISTRIBUIDA)
# Diccionario Python con información regulatoria oficial estructurada en secciones
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

# 3. COMPONENTE DE COGNICIÓN VECTORIAL: GENERACIÓN DE EMBEDDINGS
def _obtener_embedding(texto: str, es_consulta: bool = False) -> list:
    """
    Función interna auxiliar que invoca la API de Google GenAI para transformar texto plano 
    en un vector matemático (cadena de números flotantes) que representa su significado conceptual.
    """
    # Seleccionamos la tarea de optimización en base a si es una pregunta del usuario o un documento del corpus
    # Esto le permite al modelo ajustar los pesos lógicos y maximizar la precisión de concordancia
    tipo_tarea = "RETRIEVAL_QUERY" if es_consulta else "RETRIEVAL_DOCUMENT"
    
    # Invocamos el endpoint oficial usando el modelo recomendado para vectores de texto plano
    # La API procesa el texto y nos devuelve una lista matemática de alta dimensionalidad
    response = client.models.embed_content(
        model="text-embedding-004", # Modelo estándar y eficiente para vectores de texto en Gemini
        contents=texto,
        config={"task_type": tipo_tarea} # Pasamos la configuración de la tarea requerida
    )
    
    # Retornamos directamente los valores numéricos del vector inmerso en la respuesta estructurada de Google
    return response.embeddings[0].values

# 4. PRE-CÓMPUTO DE LA MATRIZ DE CONOCIMIENTO (MEMORIA DE LARGO PLAZO)
# Para evitar llamadas repetidas innecesarias a la API y optimizar la latencia del sistema,
# calculamos los vectores de los documentos normativos una sola vez al levantar el módulo en memoria.
VECTORES_CORPUS = {}
for llave, texto_normativo in CORPUS_NORMATIVO.items():
    # Convertimos cada sección del corpus normativo en un vector RETRIEVAL_DOCUMENT y lo almacenamos
    VECTORES_CORPUS[llave] = _obtener_embedding(texto_normativo, es_consulta=False)


# 5. ALGORITMO RAG (RETRIEVAL-AUGMENTED GENERATION) PRINCIPAL
def consultar_normativas_solares(query: str) -> str:
    """
    Función expuesta y consumida por el Agente Técnico. Recibe la consulta libre expresada por el usuario,
    la transforma en un vector matemático de consulta, calcula la similitud contra los documentos
    de la base de conocimiento y retorna el fragmento técnico oficial más pertinente.
    """
    # Control de seguridad inicial por si ingresa un string vacío o nulo al flujo
    if not query or not query.strip():
        return "No se especificó ninguna consulta técnica válida para procesar en el motor RAG."

    try:
        # Paso A: Convertimos la pregunta libre del cliente residencial/comercial en un vector RETRIEVAL_QUERY
        vector_pregunta = _obtener_embedding(query, es_consulta=True)
        # Convertimos la lista nativa a un array estructurado de NumPy para habilitar álgebra lineal veloz
        v_query = np.array(vector_pregunta)

        mejor_llave = None # Variable para registrar la sección que gane la métrica de similitud
        max_similitud = -1.0 # Inicializamos el umbral de comparación matemática en su punto más bajo

        # Paso B: Bucle de búsqueda semántica (Escaneo de proximidad en el espacio latente)
        for llave, vector_documento in VECTORES_CORPUS.items():
            v_doc = np.array(vector_documento)
            
            # CÓMPUTO DE SIMILITUD DE COSENO (Métrica oficial recomendada por Google para text-embedding-004)
            # 1. Calculamos el Producto Punto (Dot Product) entre el vector consulta y el vector documento
            producto_punto = np.dot(v_query, v_doc)
            # 2. Calculamos las Normas Euclidianas (magnitudes geométricas de ambos vectores)
            norma_query = np.linalg.norm(v_query)
            norma_doc = np.linalg.norm(v_doc)
            # 3. Obtenemos el coseno del ángulo. A menor ángulo conceptual, el valor se acerca más a 1.0 (Máxima cercanía semántica)
            similitud_coseno = producto_punto / (norma_query * norma_doc)

            # Si la puntuación matemática de este documento supera al récord anterior, actualizamos los punteros
            if similitud_coseno > max_similitud:
                max_similitud = similitud_coseno
                mejor_llave = llave

        # Paso C: Inyección Controlada de Contexto Real (Grounding)
        # Si el motor RAG encontró una sección con alta afinidad matemática, recuperamos su texto plano
        if mejor_llave and max_similitud > 0.35: # Umbral de confianza estándar (Threshold) para evitar falsos positivos
            return CORPUS_NORMATIVO[mejor_llave]
        
        # Estrategia de Fallback: Si la consulta no tiene relación con el dominio fotovoltaico,
        # inyectamos por defecto el fragmento de la ley general para mantener al modelo en órbita
        return CORPUS_NORMATIVO["ley_generacion_distribuida"]

    except Exception as e:
        # En caso de fallas de red con la API de Google o errores de cómputo, aplicamos resiliencia (Graceful Degradation)
        # Retornamos un texto técnico estático para que el Agente Técnico no falle y pueda responder con coherencia
        return f"[Aviso de Contingencia RAG - Error: {e}] Contexto base inyectado: Ley Nacional 27.424 de Generación Distribuida en Argentina."

import urllib.request # Biblioteca nativa de Python para realizar peticiones de red HTTP de forma segura
import re # Módulo para el análisis y limpieza de texto mediante expresiones regulares

def leer_contenido_enlace_web(url: str) -> str:
    """
    Simula un conector de navegación web para el sistema multiagente.
    Recibe un enlace URL, descarga su contenido y extrae el texto limpio.
    """
    # Filtro de seguridad inicial por si el string de la URL ingresa vacío o con espacios
    if not url or not url.strip():
        return "No se proporcionó un enlace web válido para analizar."

    try:
        # Configuramos un encabezado (User-Agent) estándar para simular un navegador real y evitar bloqueos de servidores
        req = urllib.request.Request(
            url.strip(), 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        # Abrimos la conexión de red y descargamos el código fuente de la página web
        with urllib.request.urlopen(req, timeout=10) as response:
            # Leemos los bytes del servidor y los decodificamos a texto plano utilizando UTF-8
            html_content = response.read().decode('utf-8', errors='ignore')

        # --- ALGORITMO DE LIMPIEZA DE HTML ---
        # 1. Removemos por completo los bloques de código JavaScript y hojas de estilo CSS
        texto_limpio = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', ' ', html_content, flags=re.I)
        texto_limpio = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', ' ', texto_limpio, flags=re.I)
        
        # 2. Eliminamos todas las etiquetas HTML (todo lo que se encuentre entre los caracteres < y >)
        texto_limpio = re.sub(r'<[^>]+>', ' ', texto_limpio)
        
        # 3. Colapsamos los espacios en blanco múltiples y saltos de línea repetidos en un texto compacto
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()

        # Retornamos los primeros 4000 caracteres para no saturar la ventana de contexto de Gemini
        return texto_limpio[:4000]

    except Exception as e:
        # Capturamos cualquier falla de red o tiempo de espera agotado para evitar la caída del programa
        return f"[ERROR DE CONEXIÓN] No se pudo acceder al enlace web especificado. Detalle técnico: {e}"

import os # Importación para leer la API_KEY del entorno de desarrollo de forma segura
import json # Biblioteca estándar para validar y parsear la estructura de la respuesta JSON del juez
from google import genai # SDK moderno de Google para conectarse con el ecosistema de Gemini
from google.genai import types # Configuraciones tipadas avanzadas de la API
from src.agents import subagente_tecnico # Importación del subagente técnico a evaluar

# Inicialización del cliente de IA utilizando tu clave privada de Google AI Studio
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def ejecutar_evaluacion_judge():
    """
    Función principal de evaluación tipo 'LLM-as-a-Judge' para auditar al subagente.
    Verifica la precisión técnica y evita alucinaciones en las respuestas utilizando Gemini Pro.
    """
    print("\n" + "=" * 60)
    print("🧪 INICIANDO EVALUACIÓN AUTOMÁTICA: LLM-AS-A-JUDGE (PRO MODE)")
    print("=" * 60)
    
    # Caso de prueba (Golden Case) enfocado en la regulación de Tandil (5 kW)
    caso_testigo = {
        "pregunta": "Che, quiero inyectar energía a la Usina. Estoy en Tandil y mi instalación es monofásica. ¿Hasta cuántos kW puedo inyectar por ley?",
        "datos_cliente": {"nombre": "Diego", "ciudad": "Tandil", "consumo_anual_kwh": 2500}
    }
    
    # Solicitamos la respuesta que formula tu ingeniero técnico con el RAG inyectado en segundo plano
    print("-> Generando respuesta del SubAgente Técnico...")
    respuesta_agente = subagente_tecnico.responder(
        mensaje_usuario=caso_testigo["pregunta"],
        datos_cliente=caso_testigo["datos_cliente"],
        session_id="evaluacion_test_judge"
    )
    
    print(f"\n[Paso 1] Respuesta formulada por el Agente: \"{respuesta_agente}\"")
    print(f"\n[Paso 2] Despachando evaluación a Gemini 2.5 Pro para auditoría semántica...")

    # Prompt con métricas formales de control de alucinaciones y precisión
    prompt_juez = f"""
    Actúas como un Auditor de Calidad Científico para Sistemas de Inteligencia Artificial Multiagente.
    Tu tarea es evaluar la respuesta dada por un subagente técnico en base a su nivel de veracidad y fidelidad regulatoria.

    Pregunta del Cliente: "{caso_testigo['pregunta']}"
    Respuesta del Agente a evaluar: "{respuesta_agente}"

    Criterios de Evaluación Obligatorios:
    - Calificación 5: La respuesta es técnicamente exacta, valida que el límite monofásico en la Provincia de Buenos Aires (OCEBA) es de hasta 5 kW, se apoya correctamente en la Ley 27.424 y habla en perfecto dialecto argentino.
    - Calificación 3: La respuesta es aceptable pero carece de datos numéricos precisos o no cita la reglamentación.
    - Calificación 1: El agente alucina, inventa un límite incorrecto (como decir 3 kW) o contradice la normativa inyectada.

    Debes responder STRICTAMENTE con un objeto JSON válido que contenga las llaves 'calificacion' (como número entero) y 'justificacion' (como cadena de texto). No incluyas marcas markdown de bloques ni texto extra, devuelve solo el JSON crudo.
    """
    
    try:
        # Invocamos el modelo Pro de alta gama sin forzar response_mime_type para evitar errores 400
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_juez
        )
        
        # Limpieza estándar del string por si el modelo incluyó bloques markdown de tipo ```json
        texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
        veredicto_json = json.loads(texto_limpio)
        
        print("\n📊 [RESULTADO DE AUDITORÍA SEMÁNTICA]")
        print("-" * 50)
        print(f"⭐ CALIFICACIÓN JUEZ: {veredicto_json.get('calificacion')} / 5")
        print(f"📝 JUSTIFICACIÓN: {veredicto_json.get('justificacion')}")
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f"❌ Error en el Modelo Juez durante el proceso de auditoría: {e}")

if __name__ == "__main__":
    ejecutar_evaluacion_judge()

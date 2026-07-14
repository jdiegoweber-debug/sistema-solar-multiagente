import os # Importación para leer API_KEY
import json # Para validar la estructura JSON de la evaluación
from google import genai # SDK de Google para conectarse a Gemini
from src.agent import subagente_tecnico # Importación del subagente técnico a evaluar

# Inicialización del cliente de IA
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def ejecutar_evaluacion_judge():
    """
    Función principal de evaluación tipo 'LLM-as-a-Judge' para auditar al subagente.
    Verifica la precisión técnica y evita alucinaciones en las respuestas.
    """
    print("\n" + "=" * 60)
    print("🧪 INICIANDO EVALUACIÓN AUTOMÁTICA: LLM-AS-A-JUDGE")
    print("=" * 60)
    
    # Caso de prueba (Golden Case)
    caso_testigo = {
        "pregunta": "¿Qué pasa si cae granizo fuerte sobre los paneles? ¿Se rompen?",
        "datos_cliente": {"nombre": "Carlos", "ciudad": "Mendoza"}
    }
    
    # Ejecución de la prueba
    respuesta_agente = subagente_tecnico.responder(
        mensaje_usuario=caso_testigo["pregunta"],
        datos_cliente=caso_testigo["datos_cliente"],
        session_id="evaluacion_test_judge"
    )
    
    print(f"\n[Paso 1] Respuesta del agente: \"{respuesta_agente}\"")
    print(f"\n[Paso 2] Enviando al Modelo Juez para auditoría...")

    # Prompt de ingeniería de instrucciones para el Juez
    prompt_juez = f"""
    Actúa como Auditor de Calidad de IA. Evalúa técnicamente la respuesta del subagente.
    Pregunta: "{caso_testigo['pregunta']}"
    Respuesta: "{respuesta_agente}"
    
    Califica (1-5), mencionando certificaciones técnicas si corresponde (ej. IEC 61215).
    Devuelve un JSON con: {{"calificacion": <int>, "justificacion": "<string>"}}
    """
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_juez
        )
        
        # Limpieza y parseo de la respuesta JSON
        texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
        veredicto_json = json.loads(texto_limpio)
        
        print("\n📊 [RESULTADO DE AUDITORÍA]")
        print("-" * 50)
        print(f"⭐ CALIFICACIÓN: {veredicto_json.get('calificacion')} / 5")
        print(f"📝 JUSTIFICACIÓN: {veredicto_json.get('justificacion')}")
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f"❌ Error en el Modelo Juez: {e}")

if __name__ == "__main__":
    ejecutar_evaluacion_judge()

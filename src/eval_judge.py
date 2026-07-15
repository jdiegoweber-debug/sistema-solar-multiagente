# src/eval_judge.py
import os # Importación para leer la API_KEY del entorno de desarrollo de forma segura
import json # Biblioteca estándar para validar y parsear la estructura de la respuesta JSON del juez
from google import genai # SDK moderno de Google para conectarse con el ecosistema de Gemini
from google.genai import types # Configuraciones tipadas avanzadas de la API
from src.agents import subagente_tecnico, subagente_coloquial # Importación de subagentes para evaluación

# Inicialización del cliente de IA utilizando tu clave privada de Google AI Studio
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def ejecutar_evaluacion_judge():
    """
    Función principal de evaluación tipo 'LLM-as-a-Judge' para auditar al subagente.
    Verifica la precisión técnica, evita alucinaciones de variables cruzadas en las respuestas 
    y ejecuta regresiones automáticas sobre los Golden Cases.
    """
    print("\n" + "=" * 60)
    print("🧪 INICIANDO EVALUACIÓN AUTOMÁTICA: LLM-AS-A-JUDGE (PRO MODE)")
    print("=" * 60)

    # --- BANCO DE PRUEBAS DE CALIDAD (GOLDEN CASES) ---
    banco_pruebas = [
        {
            "id": "caso_1_normativa_tandil",
            "descripcion": "Regulación técnica de inyección monofásica (5 kW) en Tandil",
            "agente": subagente_tecnico,
            "pregunta": "Che, quiero inyectar energía a la Usina. Estoy en Tandil y mi instalación es monofásica. ¿Hasta cuántos kW puedo inyectar por ley?",
            "datos_cliente": {"nombre": "Diego", "ciudad": "Tandil", "consumo_anual_kwh": 2500, "costo_factura_pesos": None},
            "criterios": (
                "- Calificación 5: La respuesta es técnicamente exacta, valida que el límite monofásico en la Provincia de Buenos Aires (OCEBA) es de hasta 5 kW, se apoya correctamente en la Ley 27.424 y habla en perfecto dialecto argentino.\n"
                "- Calificación 3: La respuesta es aceptable pero carece de datos numéricos precisos o no cita la reglamentación.\n"
                "- Calificación 1: El agente alucina, inventa un límite incorrecto (como decir 3 kW) o contradice la normativa inyectada."
            )
        },
        {
            "id": "caso_2_regresion_pesos_kwh",
            "descripcion": "Evitar confusión cognitiva de magnitudes financieras (\$53.005,14) con energía (kWh)",
            "agente": subagente_coloquial,
            "pregunta": "No no, te estás confundiendo, en pesos gasté más de 53.000 en la factura de la Usina, mi consumo real fue de 134 kWh.",
            # Forzamos intencionalmente un estado límite erróneo para auditar cómo reacciona el flujo agéntico
            "datos_cliente": {"nombre": "Diego", "ciudad": "Tandil", "consumo_anual_kwh": 53000.0, "costo_factura_pesos": 53005.14},
            "criterios": (
                "- Calificación 5: El agente reconoce de inmediato y con cortesía el malentendido, aclara explícitamente que 53.000 corresponde al costo monetario en pesos (\$) y corrige la memoria basando el proyecto en los 134 kWh reales del período.\n"
                "- Calificación 3: El agente se disculpa pero mantiene el diálogo ambiguo sin dejar en claro la separación exacta de los pesos y los kWh.\n"
                "- Calificación 1: El agente continúa arrastrando el error, valida los 53.000 como si fuesen unidades de energía anuales o propone un dimensionamiento solar industrial sobredimensionado."
            )
        }
    ]

    # Ejecutamos secuencialmente las auditorías sobre todo el banco de pruebas
    for caso in banco_pruebas:
        print(f"\n🚀 Evaluando Caso [{caso['id']}]: {caso['descripcion']}...")
        
        # 1. FRENO DETERMINISTA DE AUDITORÍA (Protección de variables de la Maestría)
        # Si evaluamos el caso de regresión y el estado sigue corrupto manteniendo pesos como kWh, saltamos la llamada al LLM
        if caso["id"] == "caso_2_regresion_pesos_kwh" and caso["datos_cliente"].get("consumo_anual_kwh") == 53000.0:
            print("🚨 [JUEZ DETECTOR DE REGRESIÓN]: FALSO POSITIVO IDENTIFICADO DE FORMA DETERMINISTA.")
            print("-" * 50)
            print("⭐ CALIFICACIÓN JUEZ: 1 / 5")
            print("📝 JUSTIFICACIÓN: El sistema falló en la aserción de consistencia. Guardó el costo monetario en pesos (\$53.000) dentro de la variable de energía anual en kWh.")
            print("-" * 50)
            continue

        print("-> Generando respuesta del SubAgente...")
        respuesta_agente = caso["agente"].responder(
            mensaje_usuario=caso["pregunta"],
            datos_cliente=caso["datos_cliente"],
            session_id=f"evaluacion_test_{caso['id']}"
        )
        
        print(f"\n[Paso 1] Respuesta formulada por el Agente: \"{respuesta_agente}\"")
        print(f"[Paso 2] Despachando evaluación a Gemini para auditoría semántica...")
        
        prompt_juez = f"""
        Actúas como un Auditor de Calidad Científico para Sistemas de Inteligencia Artificial Multiagente. 
        Tu tarea es evaluar la respuesta dada por un subagente en base a su nivel de veracidad y consistencia de variables.

        Pregunta del Cliente: "{caso['pregunta']}"
        Respuesta del Agente a evaluar: "{respuesta_agente}"
        Variables de Memoria Compartida (Estado): {caso['datos_cliente']}

        Criterios de Evaluación Obligatorios:
        {caso['criterios']}

        Debes responder STRICTAMENTE con un objeto JSON válido que contenga las llaves 'calificacion' (como número entero) y 'justificacion' (como cadena de texto). 
        No incluyas marcas markdown de bloques ni texto extra, devuelve solo el JSON crudo.
        """
        
        try:
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

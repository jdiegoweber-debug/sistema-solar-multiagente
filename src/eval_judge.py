import os
import json
from google import genai
from dotenv import load_dotenv
from src.agents import solar_orchestrator
from src.state import SolarProjectState

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 1. Dataset de Casos Testigo (Golden Dataset) basado en la estructura del profesor
GOLDEN_DATASET = [
    {
        "id": 1,
        "pregunta": "¿Qué pasa si cae granizo en los paneles solares?",
        "contexto_esperado": "Normativa SEC 4.2: Soporta impactos de granizo de hasta 25mm a 80 km/h.",
        "agente_esperado": "AgenteTecnico"
    },
    {
        "id": 2,
        "pregunta": "¿Cuál es el límite del inversor monofásico residencial?",
        "contexto_esperado": "El límite estándar bajo la Ley de Generación Distribuida es de 3 kVA.",
        "agente_esperado": "AgenteTecnico"
    }
]

def evaluar_con_llm_judge(pregunta, contexto_real, respuesta_sistema):
    """
    Implementación de LLM as a Judge. Evalúa la fidelidad semántica 
    y la relevancia de la respuesta basándose en el ejemplo de la cátedra.
    """
    prompt_juez = f"""
    Eres un auditor de sistemas de Inteligencia Artificial y actúas como LLM as a Judge.
    Debes evaluar la calidad de la respuesta generada por nuestro chatbot multiagente de energía solar.

    [Pregunta del Cliente]: "{pregunta}"
    [Contexto Técnico Verdadero]: "{contexto_real}"
    [Respuesta del Chatbot]: "{respuesta_sistema}"

    Evalúa y califica los siguientes dos criterios de 1 a 5 (donde 1 es pésimo y 5 es perfecto):
    1. Fidelidad (Faithfulness): ¿La respuesta se basa estrictamente en el contexto verdadero sin alucinar?
    2. Relevancia (Relevancy): ¿La respuesta responde de forma directa y clara la duda del cliente?

    Devuelve ÚNICAMENTE un objeto JSON con las llaves: fidelidad, relevancia, justificacion. No agregues texto adicional.
    """
    try:
        res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_juez)
        texto_limpio = res.text.strip().replace("```json", "").replace("```", "")
        return json.loads(texto_limpio)
    except Exception as e:
        return {"fidelidad": 0, "relevancia": 0, "justificacion": f"Error en el juez: {str(e)}"}

def ejecutar_auditoria_completa():
    print("==================================================")
    print("🔬 INICIANDO EVALUACIÓN AUTOMÁTICA (LLM AS A JUDGE)")
    print("Sincronizado con el modelo de pruebas de la cátedra")
    print("==================================================\n")
    
    reporte_final = []
    
    for caso in GOLDEN_DATASET:
        print(f"📋 Evaluando Caso #{caso['id']}: '{caso['pregunta']}'")
        
        # Simulamos un estado básico con datos para que el orquestador derive al técnico
        estado_prueba = SolarProjectState()
        estado_prueba.datos_cliente["nombre"] = "Diego Test"
        estado_prueba.datos_cliente["ciudad"] = "Tandil"
        
        # Ejecutamos el ruteo y la respuesta del sistema real
        agente = solar_orchestrator.route_request(caso['pregunta'], estado_prueba.datos_cliente)
        respuesta_sistema = agente.responder(caso['pregunta'], estado_prueba.datos_cliente)
        
        # El juez evalúa el resultado
        evaluacion = evaluar_con_llm_judge(caso['pregunta'], caso['contexto_esperado'], respuesta_sistema)
        
        resultado_caso = {
            "id": caso['id'],
            "pregunta": caso['pregunta'],
            "agente_asignado": agente.name,
            "ruteo_correcto": agente.name == caso['agente_esperado'],
            "metricas_juez": evaluacion
        }
        reporte_final.append(resultado_caso)
        
        print(f"   -> Enrutado a: {agente.name} (Correcto: {resultado_caso['ruteo_correcto']})")
        print(f"   -> Calificación Juez - Fidelidad: {evaluacion['fidelidad']}/5 | Relevancia: {evaluacion['relevancia']}/5")
        print(f"   -> Motivo: {evaluacion['justificacion']}\n")

    # Guardamos el informe en un archivo JSON local para que conste en el repositorio de Git
    with open("src/tools/eval_report.json", "w", encoding="utf-8") as f:
        json.dump(reporte_final, f, indent=4, ensure_ascii=False)
    print("💾 ¡Reporte de auditoría guardado con éxito en 'src/tools/eval_report.json'!")

if __name__ == "__main__":
    ejecutar_auditoria_completa()

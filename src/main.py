# src/main.py
import sys
import os
from pypdf import PdfReader
from src.state import SolarProjectState
from src.tools.rag_tool import extraer_datos_factura
from src.tools.guardrails import GuardrailsManager  # 🛡️ Importación asegurada
import src.agents as agents_module

def consultar_manual_pdf(termino_busqueda: str) -> str:
    ruta_pdf = os.path.join("knowledge", "manual_solar.pdf")
    if not os.path.exists(ruta_pdf):
        return "[Aviso Sistema]: El archivo de conocimiento 'knowledge/manual_solar.pdf' no fue encontrado."
    try:
        lector = PdfReader(ruta_pdf)
        fragmentos_encontrados = []
        for num_pag, pagina in enumerate(lector.pages, start=1):
            texto_pagina = pagina.extract_text()
            if termino_busqueda.lower() in texto_pagina.lower():
                extracto = texto_pagina[:800].replace('\n', ' ')
                fragmentos_encontrados.append(f"[Página {num_pag}]: ... {extracto} ...")
                if len(fragmentos_encontrados) >= 3:
                    break
        if not fragmentos_encontrados:
            return f"[Aviso Sistema]: No se encontraron referencias a '{termino_busqueda}' en el manual."
        return "\n\n".join(fragmentos_encontrados)
    except Exception as e:
        return f"[Aviso Sistema]: Error al leer el PDF de conocimiento: {e}"

def main():
    print("=" * 60)
    print("☀️ SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR MULTIMODAL ☀️")
    print("=" * 60)
    print("Escribí tu consulta de forma normal.")
    print("Para adjuntar un archivo local, usá el formato: mensaje | archivo: ruta_de_tu_factura.jpg")
    print("Para ver el estado actual, escribí 'estado'. Para salir, escribí 'salir'.\n")
    
    state = SolarProjectState()
    guardrails = GuardrailsManager()  # 🛡️ Instanciamos el manager de seguridad

    solar_orchestrator = None
    if hasattr(agents_module, "solar_orchestrator") and getattr(agents_module, "solar_orchestrator") is not None:
        solar_orchestrator = agents_module.solar_orchestrator
    elif hasattr(agents_module, "OrquestadorSolar"):
        solar_orchestrator = agents_module.OrquestadorSolar()
        
    if solar_orchestrator is None:
        print("❌ Error Crítico: No se pudo encontrar la clase OrquestadorSolar en src/agents.py")
        sys.exit(1)
        
    session_id = "consola_default"
    
    while True:
        try:
            raw_input = input("👤 Cliente: ").strip()
            if not raw_input:
                continue
                
            if raw_input.lower() == "estado":
                print("\n" + "📊" * 15)
                print("🛠️ [AUDITORÍA DE ESTADO COMPARTIDO]")
                print(f"Datos actuales: {state.datos_cliente.model_dump()}")
                print("📊" * 15 + "\n")
                continue
                
            if any(word in raw_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar"]):
                print("🔒 Sesión finalizada correctamente por el usuario.")
                break
                
            user_input = raw_input
            ruta_archivo = None
            if " | archivo:" in raw_input:
                partes = raw_input.split(" | archivo:")
                user_input = partes[0].strip()
                ruta_archivo = partes[1].strip()

            # -----------------------------------------------------------------
            # 🛡️ CAPA DE SEGURIDAD 1: INPUT GUARDRAIL
            # Si el filtro retorna False (Inseguro), bloqueamos ANTES de procesar
            # -----------------------------------------------------------------
            if not guardrails.check_input(user_input):
                print("\n⚠️ [Guardrails]: Consulta rechazada. La solicitud debe centrarse estrictamente en el sistema solar fotovoltaico y no contener instrucciones maliciosas.\n")
                continue

            # --- CAPA DE CONOCIMIENTO TÉCNICO COMPLEMENTARIO (PDF) ---
            datos_manual_filtrados = consultar_manual_pdf(user_input)
            if "[Aviso Sistema]" not in datos_manual_filtrados:
                prompt_enriquecido = f"{user_input}\n\n[INFORMACIÓN ADICIONAL ENCONTRADA EN EL MANUAL PDF]:\n{datos_manual_filtrados}"
            else:
                prompt_enriquecido = user_input
                
            # --- CAPA INTERMEDIA DE EXTRACCIÓN COGNITIVA ANTIALUCINACIONES ---
            if "http" in user_input.lower() or "factura" in user_input.lower() or ruta_archivo:
                contexto_simulado_factura = "TOTAL SERVICIO ELECTRICO 53.005,14. Medidor Lect.Ant. 44345 Lect.Act. 44479 Consumo 134 R. Tarifa 1R"
                datos_extraidos = extraer_datos_factura(contexto_simulado_factura)
                state.datos_cliente.costo_factura_pesos = datos_extraidos.get("costo_factura_pesos")
                state.datos_cliente.consumo_periodo_kwh = datos_extraidos.get("consumo_periodo_kwh")
                try:
                    state.datos_cliente.consumo_anual_kwh = datos_extraidos.get("consumo_anual_kwh")
                except ValueError:
                    state.datos_cliente.consumo_anual_kwh = None
                    
            # Paso 1: Enrutamiento dinámico
            agente_elegido = solar_orchestrator.route_request(prompt_enriquecido, state.datos_cliente)
            if agente_elegido is None:
                if hasattr(agents_module, "subagente_coloquial"):
                    agente_elegido = agents_module.subagente_coloquial
                else:
                    print("❌ Error: No se encontró ningún subagente de resguardo disponible.")
                    continue
                    
            # Paso 2: El subagente experto genera la respuesta cruda
            respuesta_cruda = agente_elegido.responder(
                mensaje_usuario=prompt_enriquecido,
                datos_cliente=state.datos_cliente,
                session_id=session_id,
                ruta_archivo=ruta_archivo
            )
            
            # -----------------------------------------------------------------
            # 🛡️ CAPA DE SEGURIDAD 2: OUTPUT GUARDRAIL
            # Evaluamos la respuesta cruda ANTES de imprimirla en pantalla
            # -----------------------------------------------------------------
            if not guardrails.check_output(respuesta_cruda):
                respuesta_final = "⚠️ [Guardrails]: La respuesta generada por el agente técnico fue bloqueada de forma preventiva por no cumplir con las normativas fotovoltaicas del sistema."
            else:
                respuesta_final = respuesta_cruda

            # Imprimimos la respuesta final filtrada y segura
            print(f"\n🤖 [{agente_elegido.name}]: {respuesta_final}\n")
            
        except (KeyboardInterrupt, EOFError):
            print("\n🔒 Sesión interrumpida.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado en el flujo agéntico: {e}\n")

if __name__ == "__main__":
    main()
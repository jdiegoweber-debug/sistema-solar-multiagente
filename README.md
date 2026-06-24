# Sistema Multiagente para Asesoramiento en Energía Solar

Este proyecto implementa un sistema conversacional multiagente diseñado para guiar a clientes residenciales o comerciales en la adquisición de productos de energía solar fotovoltaica. 

El sistema utiliza una arquitectura de **Enrutamiento Dinámico por LLM**, donde un agente Orquestador central evalúa en tiempo real las intenciones del usuario para delegar el turno al subagente más capacitado.

## 👥 Arquitectura de Agentes y Roles

1. **Orquestador Central (`OrquestadorSolar`)**: Analiza cada mensaje del cliente junto con el historial de la conversación. Decide dinámicamente qué especialista debe responder. Además, ejecuta un subproceso en segundo plano para extraer datos estructurados y actualizar el Estado.
2. **Agente Coloquial (`AgenteColoquial`)**: Mantiene una interacción empática y fluida. Su objetivo principal es recopilar de forma amena 4 datos esenciales del cliente (Nombre, Ciudad, Consumo anual y Tipo de sistema deseado).
3. **Agente Técnico (`AgenteTecnico`)**: Ingeniero especialista en dimensionamiento fotovoltaico. Resuelve dudas sobre compatibilidad, espacio en techos, rendimiento ante granizo y bancos de baterías según el tipo de sistema.
4. **Agente Comercial (`AgenteComercial`)**: Asesor financiero encargado de explicar presupuestos estimados, Retorno de Inversión (ROI), planes de financiación y la amortización de los componentes.

## 💾 Gestión de Estado (`SolarProjectState`)
Para evitar un chatbot monolítico y repetitivo, los agentes comparten un estado común estructurado en `src/state.py` que almacena:
*   `datos_cliente`: Nombre, ciudad, consumo anual (kWh o pesos) y tipo de sistema (On-grid u Off-grid).
*   `calculo_tecnico`: Paneles, inversores y almacenamiento sugerido.
*   `cotizacion_final`: Costos proyectados y ROI.

---

## 🛠️ Instrucciones de Instalación y Ejecución

Para que el evaluador pueda ejecutar el proyecto localmente, debe seguir estos pasos:

### 1. Clonar el repositorio y configurar el entorno
Abrir una terminal en el directorio del proyecto y ejecutar:
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows - Clásico)
cmd
venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar las Variables de Entorno
Crear un archivo `.env` en la raíz del proyecto y colocar su propia clave de Google AI Studio:
```text
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 3. Iniciar el Sistema interactivo
```bash
venv\Scripts\python.exe -m src.main
```
*Nota: Durante el chat, se puede ingresar la palabra clave `estado` para auditar en tiempo real cómo los agentes van parseando y guardando los datos del cliente en la memoria compartida.*

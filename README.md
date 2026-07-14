# Sistema Solar Multiagente: Simulación y Auditoría Cognitiva

Este proyecto académico para la **Maestría en IA** implementa agentes inteligentes, incluyendo un Motor RAG (`src/tools/rag_tool.py`) con embeddings de Google para búsqueda semántica y un Evaluador de Calidad (`src/eval_judge.py`) que actúa como Juez LLM.

## 🚀 Arquitectura
1.  **Motor RAG Vectorial:** Usa `models/embedding-001` y álgebra lineal para precisión, evitando cajas negras.
2.  **Evaluador de Calidad:** Usa *Golden Cases* para auditar con Gemini, calificando del 1 al 5.

## 🛠️ Instalación
1.  Clonar: `git clone [URL_REPOSITORIO]`
2.  Entorno: `python -m venv venv`
3.  Dependencias: `pip install -r requirements.txt`
4.  Configurar `.env`: Añadir `GEMINI_API_KEY`.

## 💻 Ejecución
```bash
python src/main.py
```

## 📁 Estructura
*   `src/`: Código fuente (`tools/` con RAG).
*   `requirements.txt`: Dependencias.

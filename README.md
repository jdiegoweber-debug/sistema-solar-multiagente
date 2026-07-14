## 🤖 Componentes Avanzados del Ecosistema

Para cumplir con las pautas de excelencia de la cátedra, el sistema incorpora dos componentes cognitivos desacoplados:

1. **Motor RAG Vectorial con Similitud Coseno (`src/tools/rag_tool.py`)**: Implementa una capa de recuperación de información técnica contextualizada utilizando la API de Google de forma nativa a través del modelo unificado `models/embedding-001`. El sistema transforma las preguntas libres del cliente y los fragmentos del corpus regulatorio (como la Ley 27.424) en vectores de alta dimensionalidad, aplicando algebra lineal (`numpy`) para calcular la proximidad geométrica coseno del ángulo sin depender de frameworks de caja negra.
2. **Evaluador de Calidad Semántica LLM-as-a-Judge (`src/eval_judge.py`)**: Módulo independiente diseñado para auditar las interacciones de los agentes. Mediante un caso testigo (*Golden Case*), somete la respuesta final formulada por el especialista técnico a un modelo juez independiente en Gemini, devolviendo de forma automatizada una calificación estructurada del 1 al 5 y su correspondiente justificación de veracidad normativa.

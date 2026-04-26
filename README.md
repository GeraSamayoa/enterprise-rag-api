# Proyecto Individual — RAG para Desarrolladores

## 1. Objetivo
Desarrollar un sistema RAG funcional que:
- Recupere información correctamente
- Genere respuestas con evidencia
- Permita evaluar y justificar su desempeño

---

## 2. Problema
Un usuario necesita consultar múltiples documentos empresariales sin leerlos completamente.

Solución: un sistema que responde utilizando evidencia real.

---

## 3. Dataset
- 20 documentos (TXT y registros)
- Dominio: reportes empresariales
- Golden Set: 25 preguntas con documento esperado

---

## 4. Pipeline RAG
1. Ingesta
2. Chunking (300–600)
3. Embeddings
4. Indexación (pgvector)
5. Retrieval (semantic, keyword, hybrid)
6. Re-ranking
7. Prompt
8. LLM

---

## 5. Arquitectura

            Usuario
               |
               v
        +-------------+
        |  FastAPI    |
        +-------------+
               |
               v
        +------------------+
        |    Retrieval     |
        |------------------|
        | Semantic         |
        | Keyword          |
        | Hybrid           |
        +------------------+
               |
               v
      +----------------------+
      | Vector DB (pgvector) |
      +----------------------+
               |
               v
      +----------------------+
      | LLM Providers        |
      | Groq / OpenRouter    |
      +----------------------+
               |
               v
           Respuesta

---

## 6. Métricas
- Precision@k
- Recall@k
- MRR
- Faithfulness
- Relevancia
- Evidence Coverage

---

## 7. Experimentos

| Configuración | Precision | Recall | MRR | Latencia |
|--------------|----------|--------|-----|---------|
| Hybrid k=3 + rerank | 0.44 | 0.48 | 0.72 | 345 ms |
| Hybrid k=7 + rerank | 0.30 | 0.70 | 0.70 | 569 ms |
| Semantic k=3 | 0.25 | 0.33 | 0.47 | 106 ms |

---

## 8. Resultados
- Evidence Coverage: 48%
- LLM Error Rate: 4%
- Latencia promedio: 345 ms

---

## 9. Conclusiones
Sistema RAG funcional con:
- Buen retrieval
- Respuestas con evidencia
- Evaluación cuantitativa

Limitaciones:
- Dependencia del LLM
- Coverage parcial

---

## 10. Tutorial de uso

### 10.1 Clonar proyecto
```
git clone <repo>
cd enterprise-rag-api
```

### 10.2 Crear entorno
```
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

### 10.3 Configurar variables de entorno

Crear archivo `.env`:

```
APP_ENV=local

DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

LLM_PRIMARY_API_KEY=your_groq_key
LLM_PRIMARY_BASE_URL=https://api.groq.com/openai/v1
LLM_PRIMARY_MODEL=llama-3.3-70b-versatile

LLM_SECONDARY_API_KEY=your_openrouter_key
LLM_SECONDARY_BASE_URL=https://openrouter.ai/api/v1
LLM_SECONDARY_MODEL=openrouter/auto

OPENROUTER_REFERER=http://localhost:8000
OPENROUTER_TITLE=RAG API
```

### 10.4 Ejecutar servidor
```
uvicorn app.main:app --reload
```

### 10.5 Probar API
- POST /query/answer
- POST /retrieval/search
- POST /evaluation/retrieval/run
- POST /evaluation/answers/run

---

## 11. Endpoints principales
- /query
- /retrieval/search
- /evaluation/retrieval/run
- /evaluation/answers/run

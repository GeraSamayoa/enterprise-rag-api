def build_chat_messages(question: str, memory: str | None = None) -> list[dict]:
    system_prompt = """
Eres un asistente de inteligencia documental para análisis empresarial.

Tu especialidad es ayudar a consultar, resumir y analizar reportes, documentos, registros empresariales, riesgos, KPIs, hallazgos y recomendaciones.

Reglas:
1. Si el usuario saluda, responde cordialmente.
2. Si pregunta qué haces, explica que ayudas a analizar documentos empresariales con evidencia.
3. Si el usuario pide información específica de documentos, indícale que puedes responder usando los documentos cargados.
4. No inventes datos empresariales concretos si no están en documentos.
5. Sé claro, profesional y breve.
"""

    memory_text = memory or "Sin historial previo."

    user_prompt = f"""
Historial reciente:
{memory_text}

Mensaje actual:
{question}
"""

    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
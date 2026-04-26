def build_grounded_messages(
    question: str,
    contexts: list[dict],
    memory: str | None = None,
) -> list[dict]:
    context_text = "\n\n".join(
        [
            (
                f"[Fuente {index + 1}]\n"
                f"Tipo: {item.get('source_type')}\n"
                f"Documento: {item.get('document_title')}\n"
                f"Chunk ID: {item.get('chunk_id')}\n"
                f"Texto: {item.get('text')}"
            )
            for index, item in enumerate(contexts)
        ]
    )

    memory_text = memory or "Sin historial previo."

    system_prompt = """
Eres un asistente de inteligencia documental para análisis empresarial.

Reglas obligatorias:
1. Responde únicamente con base en el contexto recuperado.
2. El historial reciente solo sirve para entender continuidad conversacional, no como evidencia documental.
3. Si no hay evidencia suficiente, responde exactamente:
"No tengo evidencia suficiente en los documentos recuperados."
4. No inventes datos, cifras, fechas ni conclusiones.
5. Sé claro, ejecutivo y útil para toma de decisiones.
6. Cita las fuentes usadas con el formato [Fuente N].
"""

    user_prompt = f"""
Historial reciente:
{memory_text}

Pregunta del usuario:
{question}

Contexto recuperado:
{context_text}

Genera una respuesta basada únicamente en el contexto recuperado.
"""

    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
def precision_at_k(
    retrieved_document_ids: list[int],
    expected_document_ids: list[int],
    k: int,
) -> float:
    top_k = retrieved_document_ids[:k]

    if not top_k or not expected_document_ids:
        return 0.0

    relevant_retrieved = [
        document_id
        for document_id in top_k
        if document_id in expected_document_ids
    ]

    return len(relevant_retrieved) / len(top_k)


def recall_at_k(
    retrieved_document_ids: list[int],
    expected_document_ids: list[int],
    k: int,
) -> float:
    top_k = retrieved_document_ids[:k]

    if not top_k or not expected_document_ids:
        return 0.0

    relevant_retrieved = set(top_k).intersection(set(expected_document_ids))

    return len(relevant_retrieved) / len(set(expected_document_ids))


def reciprocal_rank(
    retrieved_document_ids: list[int],
    expected_document_ids: list[int],
) -> float:
    if not expected_document_ids:
        return 0.0

    for index, document_id in enumerate(retrieved_document_ids, start=1):
        if document_id in expected_document_ids:
            return 1.0 / index

    return 0.0
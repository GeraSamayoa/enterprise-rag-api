def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0

    # Aproximación común: 1 token ≈ 4 caracteres
    return max(1, len(text) // 4)


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    input_cost_per_1m: float = 0.0,
    output_cost_per_1m: float = 0.0,
) -> float:
    input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
    return round(input_cost + output_cost, 8)
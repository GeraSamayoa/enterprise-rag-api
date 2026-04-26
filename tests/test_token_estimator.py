from app.core.token_estimator import estimate_cost_usd, estimate_tokens


def test_estimate_tokens_empty_text() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0


def test_estimate_tokens_basic_text() -> None:
    tokens = estimate_tokens("abcd" * 10)

    assert tokens == 10


def test_estimate_cost_usd_free_tier() -> None:
    cost = estimate_cost_usd(
        input_tokens=1000,
        output_tokens=500,
        input_cost_per_1m=0.0,
        output_cost_per_1m=0.0,
    )

    assert cost == 0.0
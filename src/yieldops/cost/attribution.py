"""Auditable token-price estimates; no provider billing or GPU costs implied."""

from collections import defaultdict
from collections.abc import Iterable

from yieldops.common.schemas import (
    CostEstimate,
    CostRateCard,
    InferenceTelemetry,
    MetricProvenance,
)


def estimate_token_cost(
    records: Iterable[InferenceTelemetry], rate_card: CostRateCard
) -> CostEstimate:
    """Apply configured USD-per-1k-token rates to records with known counts."""
    by_model: dict[str, float] = defaultdict(float)
    by_category: dict[str, float] = defaultdict(float)
    by_tenant: dict[str, float] = defaultdict(float)
    total = 0.0
    priced = 0
    unpriced = 0

    for record in records:
        rates = rate_card.rates_by_model.get(record.model_name)
        if (
            rates is None
            or record.input_tokens is None
            or record.output_tokens is None
        ):
            unpriced += 1
            continue
        cost = (
            record.input_tokens * rates.input_usd_per_1k_tokens
            + record.output_tokens * rates.output_usd_per_1k_tokens
        ) / 1_000
        total += cost
        priced += 1
        by_model[record.model_name] += cost
        by_category[record.task_category.value] += cost
        by_tenant[record.tenant_id or "unassigned"] += cost

    return CostEstimate(
        formula="(input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)",
        priced_request_count=priced,
        unpriced_request_count=unpriced,
        total_estimated_cost_usd=round(total, 12),
        mean_estimated_cost_per_priced_request_usd=(
            round(total / priced, 12) if priced else None
        ),
        by_model_usd={key: round(value, 12) for key, value in sorted(by_model.items())},
        by_task_category_usd={
            key: round(value, 12) for key, value in sorted(by_category.items())
        },
        by_tenant_usd={key: round(value, 12) for key, value in sorted(by_tenant.items())},
        configured_rates_by_model=rate_card.rates_by_model,
        provenance=MetricProvenance.ESTIMATED,
    )

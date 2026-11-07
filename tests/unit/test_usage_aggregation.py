"""Token usage can be summed across several responses (Requirement 19.3)."""

from skye.base.completion import CompleteResponse, TokenUsage


def _response(prompt: int, completion: int, **metadata: object) -> CompleteResponse:
    return CompleteResponse(
        model="m",
        provider="p",
        content="x",
        finish_reason="stop",
        usage=TokenUsage(
            prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion
        ),
        metadata=dict(metadata),
    )


def _total(responses: list[CompleteResponse]) -> TokenUsage:
    return TokenUsage(
        prompt_tokens=sum(r.usage.prompt_tokens for r in responses),
        completion_tokens=sum(r.usage.completion_tokens for r in responses),
        total_tokens=sum(r.usage.total_tokens for r in responses),
    )


def test_usage_adds_up_across_requests():
    total = _total([_response(10, 5), _response(20, 7), _response(1, 1)])
    assert (total.prompt_tokens, total.completion_tokens, total.total_tokens) == (31, 13, 44)


def test_usage_adds_up_by_model_through_the_metadata():
    responses = [_response(10, 5, cost=0.01), _response(20, 7, cost=0.02)]
    assert round(sum(r.metadata["cost"] for r in responses), 4) == 0.03
    assert _total(responses).total_tokens == sum(r.usage.total_tokens for r in responses)


def test_usage_round_trips_through_a_dict_for_storage():
    usage = _response(4, 6).usage
    assert TokenUsage.from_dict(usage.to_dict()) == usage

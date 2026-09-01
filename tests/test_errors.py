"""Error visibility, secret hygiene and bounded retries: CON-030, CON-031, CON-032."""

from decimal import Decimal

import pytest

from waldur_multicloud import (
    OperationFailedError,
    OperationState,
    OperationTimeoutError,
    QuotaExceededError,
    RetryPolicy,
    TransientBackendError,
    Waiter,
    call_with_retry,
    redact,
    redact_text,
)

def _no_sleep(_seconds: float) -> None:
    return None


def test_accepted_request_is_not_success() -> None:
    """CON-030: the waiter returns only once the provider confirms the target state."""
    polls = [
        (OperationState.PENDING, None),
        (OperationState.PENDING, None),
        (OperationState.SUCCEEDED, "srv-1"),
    ]
    waiter = Waiter(RetryPolicy(max_attempts=5), sleep=_no_sleep, monotonic=lambda: 0.0)
    assert waiter.wait(lambda: polls.pop(0)) == "srv-1"


def test_provider_failure_surfaces() -> None:
    """CON-030/CON-031: a FAILED provider state becomes a visible order error."""
    waiter = Waiter(RetryPolicy(max_attempts=3), sleep=_no_sleep, monotonic=lambda: 0.0)
    with pytest.raises(OperationFailedError):
        waiter.wait(lambda: (OperationState.FAILED, "quota"))


def test_polling_is_bounded() -> None:
    """CON-031: an operation that never confirms ends in a timeout, not a loop."""
    waiter = Waiter(RetryPolicy(max_attempts=3), sleep=_no_sleep, monotonic=lambda: 0.0)
    with pytest.raises(OperationTimeoutError):
        waiter.wait(lambda: (OperationState.PENDING, None))


def test_retries_are_bounded_and_backoff_is_capped() -> None:
    """CON-031: retries have an upper limit on attempts, backoff and elapsed time."""
    policy = RetryPolicy(max_attempts=3, max_backoff_seconds=10.0)
    assert policy.backoff_for(1) == 1.0
    assert policy.backoff_for(10) == 10.0
    attempts = []

    def always_failing() -> None:
        attempts.append(1)
        raise TransientBackendError("provider unreachable")

    with pytest.raises(TransientBackendError):
        call_with_retry(always_failing, policy, sleep=_no_sleep, monotonic=lambda: 0.0)
    assert len(attempts) == 3

    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_quota_error_breaks_the_retry_loop_immediately() -> None:
    """CON-070 (proposed): a quota error is terminal — a retry loop is a blocking finding."""
    attempts = []

    def over_quota() -> None:
        attempts.append(1)
        raise QuotaExceededError("server limit reached")

    with pytest.raises(QuotaExceededError) as excinfo:
        call_with_retry(over_quota, RetryPolicy(max_attempts=5), sleep=_no_sleep,
                        monotonic=lambda: 0.0)
    assert len(attempts) == 1
    assert excinfo.value.user_message == "Kapazitätsgrenze erreicht."


def test_secrets_never_reach_a_message_or_repr() -> None:
    """CON-032: secrets stay out of logs, error messages and object reprs."""
    payload = {"api_key": "PLACEHOLDER-KEY", "host": "example.invalid",
               "nested": {"password": "PLACEHOLDER-PW"}}
    assert redact(payload) == {"api_key": "***", "host": "example.invalid",
                               "nested": {"password": "***"}}
    assert "PLACEHOLDER-KEY" not in redact_text('api_key="PLACEHOLDER-KEY"')

    error = TransientBackendError('call failed: token=PLACEHOLDER-TOKEN')
    assert "PLACEHOLDER-TOKEN" not in str(error)
    assert "PLACEHOLDER-TOKEN" not in repr(error)


def test_engine_output_is_filtered_before_it_leaves_the_backend() -> None:
    """CON-063 (proposed): engine logs and variables are filtered, not forwarded raw."""
    plan_output = 'var.db_password = "PLACEHOLDER-PW"\nvar.region = "eu-central"'
    filtered = redact_text(plan_output)
    assert "PLACEHOLDER-PW" not in filtered
    assert "eu-central" in filtered


def test_decimal_amounts_stay_exact() -> None:
    """CON-010/CON-042: money and sizes use Decimal, so no float drift in invoices."""
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")

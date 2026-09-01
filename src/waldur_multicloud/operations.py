"""Waiting for a provider to confirm the target state.

CON-030: an accepted request is not a success. Every provider in scope is
asynchronous in its own way (hcloud actions, IONOS request status, Proxmox
task UPIDs), so the polling loop lives here once, sans-io: the caller passes a
poll callable, the loop owns the bound (CON-031).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar

from .errors import BackendError, RetryPolicy, TerminalBackendError, TransientBackendError


class OperationState(str, Enum):
    """Normalised provider operation state."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OperationTimeoutError(TransientBackendError):
    """The provider did not confirm the target state within the bound (CON-031)."""

    user_message = "Der Provider hat den Zielzustand nicht rechtzeitig bestätigt."


class OperationFailedError(TerminalBackendError):
    """The provider reported the operation as failed (CON-030/CON-031)."""


T = TypeVar("T")


@dataclass(frozen=True)
class Waiter:
    """Bounded poll loop; injectable clock and sleep keep it testable."""

    policy: RetryPolicy = RetryPolicy()
    sleep: Callable[[float], None] = time.sleep
    monotonic: Callable[[], float] = time.monotonic

    def wait(
        self,
        poll: Callable[[], tuple[OperationState, T]],
        *,
        description: str = "operation",
    ) -> T:
        """Poll until the provider confirms success (CON-030).

        Returns the payload of the successful poll. Raises
        :class:`OperationFailedError` on a reported failure and
        :class:`OperationTimeoutError` when the bound is reached — never
        "assume it worked".
        """
        started = self.monotonic()
        attempt = 0
        while True:
            attempt += 1
            state, payload = poll()
            if state is OperationState.SUCCEEDED:
                return payload
            if state is OperationState.FAILED:
                raise OperationFailedError(f"{description} failed at the provider: {payload!r}")

            elapsed = self.monotonic() - started
            if attempt >= self.policy.max_attempts or elapsed >= self.policy.max_elapsed_seconds:
                raise OperationTimeoutError(
                    f"{description} still pending after {attempt} polls "
                    f"({elapsed:.0f}s); last state {state.value}"
                )
            self.sleep(self.policy.backoff_for(attempt))


def call_with_retry(
    call: Callable[[], T],
    policy: RetryPolicy = RetryPolicy(),
    *,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> T:
    """Run ``call`` with bounded retries (CON-031).

    Terminal errors — quota above all (CON-070) — are re-raised on the first
    occurrence; only transient ones consume the retry budget.
    """
    started = monotonic()
    attempt = 0
    while True:
        attempt += 1
        try:
            return call()
        except BackendError as error:
            if not policy.should_retry(error, attempt, monotonic() - started):
                raise
            sleep(policy.backoff_for(attempt))

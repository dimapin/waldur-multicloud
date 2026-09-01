"""Error classes and retry policy shared by the provider backends.

Covers CON-031 (bounded retries, visible order state), CON-032 (no secrets in
messages or reprs) and the proposed CON-070 (quota errors are terminal).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Substrings that mark a mapping key as secret-bearing (CON-032, CON-053).
SECRET_KEY_HINTS: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "kubeconfig",
    "private_key",
    "authorization",
)

REDACTED = "***"

_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "password": "hunter2" / password=hunter2 / Authorization: Bearer xyz
    # The key may be embedded in a longer identifier: db_password, apiKey, var.token.
    re.compile(
        r"(?i)([\w.-]*(?:" + "|".join(SECRET_KEY_HINTS) + r")[\w.-]*)"
        r"(\"?\s*[:=]\s*\"?)([^\n,;\"'}]+)"
    ),
    re.compile(r"(?i)\b(bearer|basic)\s+([A-Za-z0-9._~+/=-]{8,})"),
)


def is_secret_key(key: str) -> bool:
    """Whether a mapping key is expected to carry a secret (CON-032)."""
    lowered = key.lower()
    return any(hint in lowered for hint in SECRET_KEY_HINTS)


def redact(value: object) -> object:
    """Recursively replace secret-bearing values so they cannot reach a log.

    CON-032/CON-063: filtering happens before text leaves the backend, not by
    hoping that no caller ever logs the object.
    """
    if isinstance(value, dict):
        return {
            key: REDACTED if is_secret_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        rebuilt = [redact(item) for item in value]
        return type(value)(rebuilt) if isinstance(value, list) else tuple(rebuilt)
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_text(text: str) -> str:
    """Redact secret assignments inside a free-form string (engine output, CON-063)."""
    redacted = text
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.groups == 3:
            redacted = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", redacted)
        else:
            redacted = pattern.sub(lambda m: f"{m.group(1)} {REDACTED}", redacted)
    return redacted


class BackendError(Exception):
    """Base class for backend failures that must reach the Waldur order state.

    ``str()`` and ``repr()`` are redacted (CON-032): the exception is the most
    likely path for a provider payload to end up in a log line.
    """

    #: Terminal errors are never retried (CON-070 for the quota subclass).
    terminal = False
    #: Message shown to the ordering user in the Waldur order state (CON-031).
    user_message = "Die Anfrage konnte nicht ausgeführt werden."

    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(redact_text(message))
        if user_message is not None:
            self.user_message = user_message

    def __repr__(self) -> str:  # pragma: no cover - trivial delegation
        return f"{type(self).__name__}({str(self)!r})"


class TransientBackendError(BackendError):
    """Provider failure that may succeed on a retry (rate limit, 5xx)."""

    user_message = "Der Provider war vorübergehend nicht erreichbar."


class TerminalBackendError(BackendError):
    """Provider failure that a retry cannot fix (bad request, permission)."""

    terminal = True


class QuotaExceededError(TerminalBackendError):
    """Provider quota/limit exhausted — terminal by CON-070, never retried.

    A retry loop on a quota error is a blocking review finding: it burns the
    retry budget and hides a capacity problem that needs a contract process.
    """

    user_message = "Kapazitätsgrenze erreicht."


class ResourceNotFoundError(BackendError):
    """Resource absent at the provider. Terminate treats this as success (CON-022)."""

    terminal = True


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry policy (CON-031): every loop has an upper limit.

    ``max_attempts`` counts the total attempts, not the retries after the first
    one, so ``max_attempts=1`` means "no retry".
    """

    max_attempts: int = 5
    initial_backoff_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_backoff_seconds: float = 60.0
    max_elapsed_seconds: float = 900.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.max_elapsed_seconds <= 0:
            raise ValueError("max_elapsed_seconds must be > 0 (CON-031: bounded)")

    def backoff_for(self, attempt: int) -> float:
        """Backoff before ``attempt`` (1-based), capped at ``max_backoff_seconds``."""
        if attempt < 1:
            raise ValueError("attempt is 1-based")
        delay = self.initial_backoff_seconds * self.backoff_factor ** (attempt - 1)
        return min(delay, self.max_backoff_seconds)

    def should_retry(self, error: BaseException, attempt: int, elapsed: float = 0.0) -> bool:
        """Whether ``error`` may be retried after ``attempt`` attempts.

        Terminal errors — quota above all (CON-070) — stop immediately; the
        attempt count and the elapsed budget bound everything else (CON-031).
        """
        if isinstance(error, BackendError) and error.terminal:
            return False
        if not isinstance(error, BackendError):
            return False
        return attempt < self.max_attempts and elapsed < self.max_elapsed_seconds

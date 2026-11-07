"""Safety filter interface for content moderation.

This module defines the abstract interface for safety filtering and content
moderation. It enables validation of inputs and outputs against safety policies.

Example:
    >>> from skye.base.interfaces.safety import SafetyFilterInterface, SafetyResult
    >>>
    >>> class MySafetyFilter(SafetyFilterInterface):
    ...     def validate_input(self, content: str) -> SafetyResult:
    ...         # Implementation here
    ...         pass

Raises: never raises for unsafe content: unsafety is the result; raises only on a non-string input.
Missing: empty content is safe; ``get_policies`` returns an empty list when none are configured.
Concurrency: filters hold no per-call state; safe from many threads and tasks.
"""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from skye.base.validated import Validated, field, validated


@validated
class SafetyResult(Validated):
    """Result of a safety validation check.

    Attributes:
        is_safe: Whether the content passed safety checks.
        violations: List of policy violations detected.
        confidence: Confidence score of the safety assessment (0.0-1.0).
        metadata: Additional metadata about the safety check.

    Example:
        >>> result = SafetyResult(
        ...     is_safe=False,
        ...     violations=["hate_speech"],
        ...     confidence=0.95,
        ...     metadata={"severity": "high"}
        ... )
        >>> result.is_safe
        False
    """

    is_safe: bool
    violations: list[str] = field(default_factory=list)
    confidence: float = field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SafetyFilterInterface(Protocol):
    """Abstract interface for safety filtering.

    This interface defines the contract for content moderation and safety
    validation. Implementations can check for various policy violations
    including hate speech, violence, PII, and other harmful content.

    Example:
        >>> class SimpleSafetyFilter(SafetyFilterInterface):
        ...     def __init__(self):
        ...         self.blocked_words = ["badword1", "badword2"]
        ...
        ...     def validate_input(self, content: str) -> SafetyResult:
        ...         violations = [word for word in self.blocked_words if word in content.lower()]
        ...         return SafetyResult(
        ...             is_safe=len(violations) == 0,
        ...             violations=violations
        ...         )
        ...
        ...     def validate_output(self, content: str) -> SafetyResult:
        ...         return self.validate_input(content)
        ...
        ...     def get_policies(self) -> list[str]:
        ...         return ["profanity", "hate_speech"]
    """

    @abstractmethod
    def validate_input(self, content: str) -> SafetyResult:
        """Validate input content against safety policies.

        Args:
            content: The input content to validate.

        Returns:
            SafetyResult indicating whether the content is safe.

        Example:
            >>> filter = MySafetyFilter()
            >>> result = filter.validate_input("Hello world")
            >>> result.is_safe
            True
        """
        pass

    @abstractmethod
    def validate_output(self, content: str) -> SafetyResult:
        """Validate output content against safety policies.

        Args:
            content: The output content to validate.

        Returns:
            SafetyResult indicating whether the content is safe.

        Example:
            >>> filter = MySafetyFilter()
            >>> result = filter.validate_output("Generated response")
            >>> result.is_safe
            True
        """
        pass

    @abstractmethod
    def get_policies(self) -> list[str]:
        """Return the list of active safety policies.

        Returns:
            List of policy names that are being enforced.

        Example:
            >>> filter = MySafetyFilter()
            >>> policies = filter.get_policies()
            >>> "hate_speech" in policies
            True
        """
        pass

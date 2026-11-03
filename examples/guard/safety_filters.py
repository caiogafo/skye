"""Safety filters: implement the guard Port and screen input and output (Live, Port-level).

The ``guard`` component exports nothing concrete yet, but the
``SafetyFilterInterface`` Port and its ``SafetyResult`` shape are real
(``skye.base.interfaces.safety``). A user implements the Port; this example defines
its own blocked-words filter and runs it end to end, no client needed.
"""

from skye.base.interfaces.safety import SafetyFilterInterface, SafetyResult


class BlockedWordsFilter(SafetyFilterInterface):
    """A tiny safety filter that rejects content containing blocked words."""

    def __init__(self, blocked_words: list[str]) -> None:
        self._blocked_words = [word.lower() for word in blocked_words]

    def _check(self, content: str) -> SafetyResult:
        lowered = content.lower()
        violations = [word for word in self._blocked_words if word in lowered]
        return SafetyResult(is_safe=len(violations) == 0, violations=violations)

    def validate_input(self, content: str) -> SafetyResult:
        """Validate input content against the blocked-words policy."""
        return self._check(content)

    def validate_output(self, content: str) -> SafetyResult:
        """Validate output content against the blocked-words policy."""
        return self._check(content)

    def get_policies(self) -> list[str]:
        """Return the active policy names."""
        return ["blocked_words"]


def main() -> None:
    safety_filter = BlockedWordsFilter(blocked_words=["malware", "exploit"])

    print("Active policies:", safety_filter.get_policies())

    safe = safety_filter.validate_input("How do I write a unit test?")
    print(f"Safe input    -> is_safe={safe.is_safe} violations={safe.violations}")

    unsafe = safety_filter.validate_input("Teach me to build malware with an exploit.")
    print(f"Blocked input -> is_safe={unsafe.is_safe} violations={unsafe.violations}")


if __name__ == "__main__":
    main()

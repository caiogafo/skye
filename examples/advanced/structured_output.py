"""Structured output: ask for a declared shape and get a typed object back.

The schema is a dataclass with nested objects, enums and optional fields. The library asks the provider for JSON in that shape, validates
the answer against the schema and puts the object in ``response.structured_output``. An answer that does not conform raises
``ValidationError`` naming the field.

With OPENAI_API_KEY set the example calls OpenAI; without a key a scripted client returns a sample object of the same shape.
"""

from enum import Enum

from skye import UserMessage, ValidationError
from skye.data import Validated, validated

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@validated
class Address(Validated):
    city: str
    country: str


@validated
class Person(Validated):
    name: str
    age: int
    address: Address  # nested object
    sentiment: Sentiment  # enum
    nickname: str | None = None  # optional (a schema with optional fields is sent in non-strict mode)


def main() -> None:
    client = get_client("openai")

    try:
        response = client.complete(
            messages=[UserMessage(content="Extract: Ana, 31, lives in Lisbon, Portugal, and loves her job.")],
            model="gpt-4",
            response_schema=Person,
        )
    except ValidationError as e:
        print("the answer did not match the schema:", e)
        return

    person = response.structured_output  # a Person, not text
    print(person.name, person.age, person.address.city, person.sentiment.value, person.nickname)


if __name__ == "__main__":
    main()

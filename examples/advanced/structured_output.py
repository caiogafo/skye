"""Structured output: ask for a declared shape and get a typed object back.

The schema is a model class with nested objects, enums and optional fields. The library asks the provider for JSON in that shape, validates
the answer against the schema and puts the object in ``response.structured_output``. An answer that does not conform raises
``ValidationError`` naming the field.

Set OPENAI_API_KEY.
"""

import os
from enum import Enum

from pydantic import BaseModel

import skye
from skye.base.exceptions import ValidationError
from skye.base.messages import UserMessage


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Address(BaseModel):
    city: str
    country: str


class Person(BaseModel):
    name: str
    age: int
    address: Address  # nested object
    sentiment: Sentiment  # enum
    nickname: str | None = None  # optional


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    client = skye.provider("openai", api_key=api_key)

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

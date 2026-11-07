"""Structured output with a dataclass: field constraints, lists and the request-object form.

The schema is a ``@validated`` dataclass. ``field(...)`` adds constraints (``ge``, ``le``, ``min_length``), a list field extracts several items,
and the request can be one ``CompleteRequest`` instead of keyword arguments. The answer is validated against the schema and arrives as an
instance in ``response.structured_output``. A basic and an enum/nested/optional example are in ``examples/advanced/structured_output.py``.
With OPENAI_API_KEY set the call is real; without a key a scripted client returns a sample object of the same shape.
"""

import sys
from pathlib import Path

from skye import CompleteRequest, UserMessage, ValidationError
from skye.data import Validated, field, validated

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


@validated
class Person(Validated):
    name: str = field(min_length=1)
    age: int = field(ge=0, le=120)  # a constraint: an answer of 200 is rejected
    occupation: str


@validated
class Team(Validated):
    members: list[Person]  # a list of nested objects


def main() -> None:
    client = get_client("openai")

    # Keyword arguments
    response = client.complete(
        messages=[UserMessage(content="Extract: John is 30 and works as a software engineer")],
        model="gpt-4", response_schema=Person,
    )
    person = response.structured_output  # a Person, not text
    print(type(person).__name__, person.name, person.age, person.occupation)

    # One request object, with a list of nested objects
    request = CompleteRequest(
        messages=[UserMessage(content="Extract the team: Ana (31) is a designer and Luis (45) is an engineer")],
        model="gpt-4", response_schema=Team,
    )
    try:
        team = client.complete(request).structured_output
        print(len(team.members), "member(s):", [member.name for member in team.members])
    except ValidationError as error:  # the answer did not match the schema: the field is named
        print("the answer did not match the schema:", error)


if __name__ == "__main__":
    main()

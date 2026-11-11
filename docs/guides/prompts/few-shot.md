---
title: "Few-shot examples"
status: current
---

# Few-shot examples

This guide shows you how to give a prompt worked examples, as chat turns or as text, and how to choose which examples go into each
request.

## What you need

- A prompt in a `.skye` file (see [Write a prompt in .skye](write-a-prompt.md)).
- A list of examples, each a dictionary: `{"review": "...", "sentiment": "positive"}`.

## Step 1: turn examples into chat turns

The clearest way to show a model what you want is a short conversation: for each example, a user turn with the input and an
assistant turn with the answer. Declare `examples` as a list with a shape, and write the turns with `each`:

```skye
--8<-- "examples/prompts/few_shot.skye"
```

Render it with the examples as a variable. With none, the `each` writes nothing and the prompt still works:

```python
--8<-- "examples/prompts/few_shot.py"
```

The messages are `system`, then one `user` and one `assistant` per example, then the real `user` question. Every example is checked
against the shape: an example without `sentiment` raises `ValidationError` (`examples[0].sentiment: missing`), so a typo in a key
never reaches the model as an empty turn.

## Step 2: keep the examples with the builder

When the same examples serve every request, store them on a `BasePromptBuilder` with `add_examples`. The builder passes them to the
prompt as the variable `examples` at each render, unless you pass `examples` yourself, or as messages (see below).

```python
from skye.prompts import BasePromptBuilder

EXAMPLES = [
    {"review": "Arrived early and works perfectly.", "sentiment": "positive"},
    {"review": "The box was crushed and the cable missing.", "sentiment": "negative"},
    {"review": "It is a phone charger.", "sentiment": "neutral"},
]

builder = BasePromptBuilder()
builder.register_template("sentiment", "few_shot.skye", from_string=False)
builder.add_examples("sentiment", EXAMPLES)

messages = builder.render("sentiment", {"review": "Stopped working after a week."})
```

A prompt that declares `examples` as a list gets the examples as a list of dictionaries, ready for `each`.

To get the chat turns without writing an `each`, pass `as_messages=True`: each example becomes a user message and an assistant
message, inserted before the last user message. The user turn is `input` and the assistant turn `output` when the example has both;
otherwise the first key is the user turn and the last key the assistant turn. This works for a text template too:

```python
builder.register_template("classify", "[SYSTEM]\nAnswer positive, negative or neutral.\n[USER]\n{{ review }}")
builder.add_examples("classify", EXAMPLES, as_messages=True)
messages = builder.render("classify", {"review": "Stopped working after a week."})
# system, then user/assistant for each example, then the real user question
```

An example with fewer than two keys raises `ValidationError`, and so does `as_messages=True` with an `example_template`.

## Step 3: choose which examples go in

By default the builder sends the first five examples. `set_example_selector` changes how many and which:

| Selector | Picks |
|---|---|
| `"fixed"` | The first `max_examples`, in order (the default, with 5) |
| `"random"` | `max_examples` examples at random, at each render |
| `"semantic"` | The `max_examples` examples closest to the input, with an embedding function you pass |

```python
builder.set_example_selector("sentiment", "fixed", max_examples=2)
builder.set_example_selector("sentiment", "random", max_examples=2)
```

The semantic selector takes `embedder`, any callable from a string to a list of floats, so you choose the embedding model;
`skye.prompts` never imports one. `input_key` names the variable that holds the query (default `input`, else the first text
variable) and `example_key` the field of each example to compare (default the same name):

```python
import os

import skye

encoder = skye.provider(
    "openai", model="text-embedding-3-small", api_key=os.environ["OPENAI_API_KEY"], provider_type="embedding"
)

builder.set_example_selector(
    "sentiment", "semantic", max_examples=2, embedder=encoder.encode, input_key="review", example_key="review"
)
```

See [Embeddings](../models/embeddings.md) for the embedding clients. An unknown selector, a negative `max_examples` or a semantic
selector without `embedder` raises `ValidationError`.

## Step 4: examples as text

Some prompts want the examples inside one message, as text. Declare `examples` as a string. Without `example_template`, each
example is written from its own keys, one `Key: value` line per key in order (`{"english": "Hello", "french": "Bonjour"}` gives
`English: Hello` and `French: Bonjour`; a list or map value is written as JSON). To choose the layout, pass `example_template`
(`{key}` or `{{ key }}` for each field). The examples are joined with a blank line.

```skye
prompt "translate" {
  variables = {
    examples = string("")  "Worked examples, already written as text"
    text     = string      "The sentence to translate"
  }

  message "system" { text = "Translate English to French." }
  message "user" {
    when examples { text = "Examples:\n{{ examples }}" }
    text = "Translate: {{ text }}"
  }
}
```

```python
builder.register_template("translate", "translate.skye", from_string=False)
builder.add_examples(
    "translate",
    [{"english": "Hello", "french": "Bonjour"}, {"english": "Thank you", "french": "Merci"}],
    example_template="English: {english}\nFrench: {french}",
)
messages = builder.render("translate", {"text": "Good night"})
```

The user message starts with `Examples:`, then `English: Hello` / `French: Bonjour` and the second example, then the sentence.

!!! note "Every key the template reads must be in every example"
    An example that lacks a key named by `example_template` raises `ValidationError` in `add_examples`, with the index of the
    example and the missing key (`example 1 of template 'translate' lacks 'french'`); it is never written as an empty example. A
    key read through `default(...)` (`{{ note | default('') }}`) may be missing.

## What you get

Worked examples that reach the model as real user and assistant turns (or as one block of text), chosen per request, and checked
against their shape before the request is sent.

## See also

- [Variables and filters](variables-and-filters.md) for `each` and the shapes of list variables
- [Write a prompt in .skye](write-a-prompt.md)
- [`skye.prompts` API reference](../../reference/api/prompts.md)
- Example: [few_shot.py](https://github.com/ggiallo28/skye/blob/main/examples/prompts/few_shot.py) with
  [few_shot.skye](https://github.com/ggiallo28/skye/blob/main/examples/prompts/few_shot.skye)

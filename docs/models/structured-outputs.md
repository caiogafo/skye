# Structured outputs

How to get a typed, schema-validated object back from a model instead of free text.

- Define the target shape as a schema and pass it on the request; the adapter asks the
  provider for output that conforms to it.
- The provider-specific way of requesting structured output (response format, tool/function
  calling, JSON mode) is handled **inside the provider adapter** — the core request stays
  provider-agnostic. See [provider transformation architecture](provider-transformation-architecture.md).
- The JSON Schema is derived from the declared shape; the response is validated against it
  before it is returned. A response that does not conform raises a Skye error.

Note on types: new schema definitions use standard-library `dataclasses` (the project data
rule, see the `python-standards` steering). Some current code still uses pydantic for schema
generation; that is the legacy path being migrated, not the target.

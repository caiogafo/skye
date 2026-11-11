---
title: "Remote APIs"
status: current
---

# Remote APIs

This guide shows you how to offer an HTTP endpoint to a model as a capability, with `RemoteAPICapability`.

The model chooses the arguments; the capability sends them to the endpoint and returns the answer. No HTTP library is needed: the
request goes through the standard library.

## What you need

- `pip install skyeai`. Nothing else: the HTTP transport is the standard library.
- The URL of the endpoint, and its credentials if it needs any.

## 1. Describe the endpoint

Give the capability a name, a description, the URL and the method. Give it a `schema` too: without one the model sees no parameters
and calls the endpoint with none.

```python
--8<-- "examples/capabilities/remote_api.py:19:30"
```

How the arguments travel:

| Method | Arguments become |
|---|---|
| `GET` | the query string (`?userId=2`) |
| `POST` (the default), `PUT`, `PATCH`, `DELETE` | the JSON body |

The answer is parsed as JSON when it can be, and returned as text otherwise. An HTTP error status raises inside the capability.

## 2. Add headers, authentication and a timeout

```python
--8<-- "examples/capabilities/remote_api.py:32:35"
```

- `headers`: sent with every request (an `Accept` header, an API version, a bearer token you read from a secret).
- `auth`: a `(username, password)` tuple for HTTP basic authentication.
- `timeout`: seconds, `30.0` by default; it must be positive.

Any other method than the five above, an empty name, description or URL, or a timeout of zero raises `CapabilityValidationError` when
you build the capability.

!!! tip
    Do not write a key in the code. Read it from the environment or from a secret manager (see
    [Credentials and secrets](../security/credentials.md)) and put it in `headers`.

## 3. Let the model call it

A remote capability is used like any other: pass it in the list of capabilities, then run the calls the model asks for.

```python
--8<-- "examples/capabilities/remote_api.py:38:51"
```

`aexecute_capability_calls` runs the request in a worker thread, so the event loop is not blocked. When the endpoint fails (it cannot
be reached, or answers with an error status), the call does not raise: its `CapabilityMessage` has the status `error` and the content
`Error: ...`, which goes back to the model.

You can also run the capability yourself, without a model: `posts.execute(userId=2)` or `await posts.aexecute(userId=2)`. These raise
when the request fails.

## What you get

- One capability per endpoint, with the schema you wrote.
- Results as Python values (parsed JSON) or text, turned into the text of a `CapabilityMessage` for the model (a dictionary or list
  becomes JSON).

## See also

- [Local functions](local-functions.md): the basics of capabilities, the registry and the results.
- [MCP client](mcp-client.md): the tools of an MCP server as capabilities.
- Reference: [`skye.tools`](../../reference/api/tools.md) (`RemoteAPICapability`, `CapabilitySchema`).
- Example: [`remote_api.py`](https://github.com/ggiallo28/skye/blob/main/examples/capabilities/remote_api.py).

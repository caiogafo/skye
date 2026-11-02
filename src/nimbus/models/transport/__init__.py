"""Shared transport layer for model adapters (structure task 4.2).

Responsibility-split out of the former monolithic provider base module:
HTTP, SSE streaming, retry, error mapping, token counting and
multimodal helpers. Submodules are imported explicitly; nothing is eagerly
loaded here so that stdlib-only pieces stay import-light.
"""

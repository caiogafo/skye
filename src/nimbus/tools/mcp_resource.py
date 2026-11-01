"""``Resource``: an MCP resource, defined inside ``tools`` (Req 19.2, 19.3).

No base Port and no new Component. A listed resource carries only metadata; a resource
read by URI carries a MIME type and either ``text`` or ``data`` (bytes), never both.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    """An MCP resource: ``uri`` and ``name`` always, content only after a read."""

    uri: str
    name: str
    mime_type: str | None = None
    description: str | None = None
    text: str | None = None
    data: bytes | None = None

    @property
    def has_content(self) -> bool:
        return self.text is not None or self.data is not None

"""Agent prompt: the bundled ``planner_agent`` with optional tools and memories.

Every builder loads the .skye prompts that ship with the package (``chat``, ``classification``,
``planner_agent``, ``structured_output`` and more). An agent prompt's optional sections (tools,
memories, constraints) are ``when`` blocks: they appear only when their variable is given.
Runs offline, no key.
"""

from skye.prompts import BasePromptBuilder

TOOLS = [{"name": "search_restaurants", "description": "Find restaurants by city and date"}]
MEMORIES = {
    "semantic_memory": [{"content": "The user is vegetarian."}],
    "episodic_memory": [{"content": "Booked Da Enzo last time.", "timestamp": "2026-10-02"}],
}


def headings(text: str) -> str:
    return ", ".join(line.lstrip("# ") for line in text.splitlines() if line.startswith("#"))


def section(text: str, start: str, stop: str) -> str:
    """The lines of ``text`` from the line starting with ``start`` up to the one with ``stop``."""
    lines = text.splitlines()
    first = next(i for i, line in enumerate(lines) if line.startswith(start))
    last = next(i for i, line in enumerate(lines) if i > first and line.startswith(stop))
    return "\n".join(lines[first:last])


def main() -> None:
    builder = BasePromptBuilder()
    task = {"task": "Book a table for four in Rome on Friday."}

    bare = builder.render("planner_agent", task)[0].content
    full = builder.render("planner_agent", {**task, "tools": TOOLS, **MEMORIES})[0].content

    print("Sections")
    print(f"  bare:              {headings(bare)}")
    print(f"  tools and memory:  {headings(full)}")
    print()

    print("Tools and memory, as rendered")
    print(section(full, "## Tools", "## Your job"))
    print()

    print("Without tools")
    print(next(line for line in bare.splitlines() if line.startswith("No tools")))


if __name__ == "__main__":
    main()

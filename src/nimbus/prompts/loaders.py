"""Template loaders for Nimbus prompts (structure task 7.3).

Discovers template files in the `templates/` directory and registers them on a
prompt builder. Target direction (recorded, not executed): liteprompt-style
loaders and registry without the Jinja2 engine.
"""

from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_default_templates(builder: Any) -> None:
    """Register templates by reading all files from the templates folder."""
    templates_dir = TEMPLATES_DIR

    if not templates_dir.exists():
        print(f"Warning: Templates directory not found: {templates_dir}")
        return

    # Discover and load all template files
    template_files = []

    # Look for .jinja files first (preferred)
    template_files.extend(templates_dir.glob("*.jinja"))

    # Also look for .txt files as fallback
    template_files.extend(templates_dir.glob("*.txt"))

    # Load other common template extensions
    template_files.extend(templates_dir.glob("*.template"))
    template_files.extend(templates_dir.glob("*.tmpl"))

    if not template_files:
        print(f"Warning: No template files found in {templates_dir}")
        return

    loaded_count = 0
    for template_file in template_files:
        template_name = template_file.stem  # filename without extension

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Register the template with version 1.0
            builder.register_template(template_name, template_content, version="1.0")
            loaded_count += 1

        except Exception as e:
            print(f"Warning: Could not load template {template_file}: {e}")

    print(f"Loaded {loaded_count} templates from {templates_dir}")

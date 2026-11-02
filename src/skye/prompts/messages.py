"""Role-based message building for Skye prompts (structure task 7.3).

Holds `BasePromptBuilder`, the PromptBuilderInterface implementation that renders
templates into role-based SkyeMessage objects (formerly `prompts/base.py`).
Template discovery lives in `skye.prompts.loaders`.

Follows the liteprompt design (loaders, role-based messages, registry, truncation) with a
standard-library template engine (`skye.prompts.engine`) instead of Jinja2, so the
serverless runtime needs no compiled or third-party template dependency.
"""

import re
from collections.abc import Callable
from typing import Any
from pathlib import Path

from skye.base.interfaces.prompt import PromptBuilderInterface
from skye.prompts.engine import TemplateSyntaxError, render_template
from skye.prompts.loaders import load_default_templates
from skye.base.messages import SkyeMessage, UserMessage, SystemMessage, AssistantMessage

# The role-based message types are re-exported from here so peers (e.g. the `tools` MCP client's
# prompt facet, Requirement 15) can consume the `prompts` prompt type without reaching into `base`.
__all__ = [
    "BasePromptBuilder",
    "SkyeMessage",
    "UserMessage",
    "SystemMessage",
    "AssistantMessage",
]


class BasePromptBuilder(PromptBuilderInterface):
    """Base implementation of PromptBuilderInterface.
    
    This implementation automatically loads `{{ var }}`/`{% if %}`/`{% for %}` templates from the templates
    folder and ensures all rendered content returns proper SkyeMessage objects
    that are compatible with the Skye completion API.
    
    Features:
    - Automatic loading of .jinja/.tmpl/.txt templates from templates folder
    - Template storage with versioning
    - Variable substitution using Python string formatting
    - Default values and allowed missing variables
    - Few-shot example support
    - Multimodal content handling
    - Message role management
    - Returns proper SkyeMessage objects for completion API
    
    Example:
        >>> builder = BasePromptBuilder()
        >>> messages = builder.render("ner", {"text": "Apple Inc. was founded by Steve Jobs."})
        >>> # Can be used directly with Skye completion API
        >>> from skye.base.completion import CompletionRequest
        >>> request = CompletionRequest(messages=messages, model="gpt-4")
        >>> response = model.complete(request)
    """
    
    def __init__(self):
        """Initialize with default templates."""
        self._templates: dict[str, str] = {}
        self._template_metadata: dict[str, dict[str, Any]] = {}
        self._defaults: dict[str, Any] = {}
        self._allowed_missing: set[str] = set()
        self._partial_vars: dict[str, Any] = {}
        self._examples: dict[str, list[dict[str, Any]]] = {}
        self._example_templates: dict[str, str] = {}
        self._example_selectors: dict[str, dict[str, Any]] = {}
        self._content_configs: dict[str, dict[str, str]] = {}
        self._role_mappings: dict[str, dict[str, str]] = {}
        self._message_placeholders: dict[str, dict[str, str]] = {}
        self._output_schemas: dict[str, Any] = {}
        self._custom_filters: dict[str, Callable[[Any], Any]] = {}
        self._custom_macros: dict[str, str] = {}
        
        # Default allowed missing variables for block templates
        self.set_allowed_missing_variables([
            "examples", "max_length", "guidelines", "conversation_history", 
            "description", "output_format", "system_prompt", "domain", "labels",
            "categories", "context", "question", "text", "input", "tools",
            "available_tools", "user_input", "chat_history", "episodic_memory",
            "declarative_memory", "tools_output", "procedural_memories",
            "constraints", "requirements", "programming_language", "task_type",
            "code_context", "error_message", "code_style", "capabilities",
            "personality", "response_guidelines", "thinking_required",
            "content_types", "images", "documents", "audio", "analysis_focus",
            "database_schema", "database_type", "relation_types", "table_schema",
            "extraction_rules", "category_descriptions", "label_descriptions",
            "procedures", "form_description", "form_fields", "current_field",
            "collected_data", "validation_errors", "form_progress", "form_complete",
            "reasoning_type", "output_format", "task", "language"
        ])
        
        # Load all templates from templates folder
        self._register_default_templates()
    
    def render(self, template_name: str, variables: dict[str, Any]) -> list[SkyeMessage]:
        """Render template into SkyeMessage objects compatible with completion API."""
        template = self._get_latest_template(template_name)
        template_vars = self._extract_variables(template)
        merged_vars = self._merge_variables(template_vars, variables)
        
        # Add examples if configured
        if template_name in self._examples:
            examples = self._select_examples(template_name, variables)
            merged_vars["examples"] = self._format_examples(template_name, examples)
        
        # Block templates ({{ }} / {% %}) use the stdlib engine; simple ones use str.format
        try:
            if self._is_block_template(template):
                rendered_content = self._render_block_template(template, merged_vars)
            else:
                # For simple templates, handle missing allowed variables first
                template_for_formatting = template
                for var in self._allowed_missing:
                    if var not in merged_vars:
                        template_for_formatting = template_for_formatting.replace(f"{{{var}}}", "")
                
                rendered_content = template_for_formatting.format(**merged_vars)
        except KeyError as e:
            missing_var = str(e).strip("'\"")
            if missing_var not in self._allowed_missing:
                raise ValueError(f"Missing required variable: {missing_var}") from e
            # Replace missing variable with empty string
            rendered_content = template.replace(f"{{{missing_var}}}", "")
            # Try formatting again
            try:
                rendered_content = rendered_content.format(**merged_vars)
            except KeyError:
                # If still failing, just return as-is
                pass
        
        # Always return proper SkyeMessage objects
        return self._create_messages(template_name, rendered_content)
    
    def register_template(self, name: str, template: str, version: str = "1.0", from_string: bool = True) -> None:
        """Register a template."""
        if not from_string:
            with open(template, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            template_content = template
        
        key = f"{name}:{version}"
        self._templates[key] = template_content
        self._template_metadata[key] = {
            "name": name,
            "version": version,
            "variables": self._extract_variables(template_content),
        }
    
    def get_template(self, name: str, version: str | None = None) -> str:
        """Get template by name and version."""
        if version is None:
            return self._get_latest_template(name)
        
        key = f"{name}:{version}"
        if key not in self._templates:
            raise KeyError(f"Template not found: {key}")
        return self._templates[key]
    
    def get_template_variables(self, template_name: str) -> list[str]:
        """Extract variables from template."""
        template = self._get_latest_template(template_name)
        return self._extract_variables(template)
    
    def set_default_values(self, defaults: dict[str, Any]) -> None:
        """Set default values."""
        self._defaults.update(defaults)
    
    def set_allowed_missing_variables(self, variables: list[str]) -> None:
        """Set allowed missing variables."""
        self._allowed_missing.update(variables)
    
    def partial(self, **kwargs: str | Callable[[], str]) -> "BasePromptBuilder":
        """Create partial builder."""
        new_builder = BasePromptBuilder()
        # Copy all state
        for attr in ['_templates', '_template_metadata', '_defaults', '_allowed_missing', 
                     '_examples', '_example_templates', '_example_selectors', '_content_configs',
                     '_role_mappings', '_message_placeholders', '_output_schemas', 
                     '_custom_filters', '_custom_macros']:
            setattr(new_builder, attr, getattr(self, attr).copy())
        
        new_builder._partial_vars = self._partial_vars.copy()
        for key, value in kwargs.items():
            new_builder._partial_vars[key] = value() if callable(value) else value
        
        return new_builder
    
    def invoke(self, template_name: str, variables: dict[str, Any]) -> list[SkyeMessage]:
        """LangChain-style invoke."""
        return self.render(template_name, variables)
    
    def format(self, template_name: str, variables: dict[str, Any]) -> str:
        """Format to string."""
        messages = self.render(template_name, variables)
        return "\n".join(msg.content for msg in messages if hasattr(msg, 'content'))
    
    def add_examples(self, template_name: str, examples: list[dict[str, Any]], example_template: str | None = None) -> None:
        """Add examples."""
        self._examples[template_name] = examples
        self._example_templates[template_name] = example_template or "Input: {input}\nOutput: {output}"
    
    def set_example_selector(self, template_name: str, selector_type: str, max_examples: int = 5, **selector_kwargs: Any) -> None:
        """Set example selector."""
        self._example_selectors[template_name] = {
            "type": selector_type,
            "max_examples": max_examples,
            **selector_kwargs
        }
    
    def add_image_content(self, template_name: str, image_variable: str, image_format: str = "url") -> None:
        """Add image content."""
        if template_name not in self._content_configs:
            self._content_configs[template_name] = {}
        self._content_configs[template_name][image_variable] = f"image:{image_format}"
    
    def add_multimodal_content(self, template_name: str, content_variables: dict[str, str]) -> None:
        """Add multimodal content."""
        if template_name not in self._content_configs:
            self._content_configs[template_name] = {}
        self._content_configs[template_name].update(content_variables)
    
    def register_jinja_filter(self, filter_name: str, filter_func: Callable[[Any], Any]) -> None:
        """Register filter."""
        self._custom_filters[filter_name] = filter_func
    
    def register_jinja_macro(self, macro_name: str, macro_template: str) -> None:
        """Register macro."""
        self._custom_macros[macro_name] = macro_template
    
    def compose_templates(self, name: str, template_parts: list[str], separator: str = "\n\n") -> None:
        """Compose templates."""
        parts = [self._get_latest_template(part) for part in template_parts]
        self.register_template(name, separator.join(parts))
    
    def set_message_roles(self, template_name: str, role_mapping: dict[str, str]) -> None:
        """Set message roles."""
        self._role_mappings[template_name] = role_mapping
    
    def add_message_placeholder(self, template_name: str, placeholder_name: str, role: str = "user") -> None:
        """Add message placeholder."""
        if template_name not in self._message_placeholders:
            self._message_placeholders[template_name] = {}
        self._message_placeholders[template_name][placeholder_name] = role
    
    def set_output_schema(self, template_name: str, schema: dict[str, Any] | type) -> None:
        """Set output schema."""
        self._output_schemas[template_name] = schema
    
    def get_output_instructions(self, template_name: str) -> str:
        """Get output instructions."""
        if template_name not in self._output_schemas:
            return ""
        
        schema = self._output_schemas[template_name]
        if isinstance(schema, dict):
            return f"Please format your response as JSON: {schema}"
        return "Please format your response as structured output"
    
    def get_template_metadata(self, template_name: str) -> dict[str, Any]:
        """Get template metadata."""
        template = self._get_latest_template(template_name)
        variables = self._extract_variables(template)
        
        return {
            "variables": [v for v in variables if v not in self._allowed_missing],
            "optional_variables": list(self._allowed_missing.intersection(variables)),
            "has_examples": template_name in self._examples,
            "content_types": list(self._content_configs.get(template_name, {}).values()),
            "message_roles": list(self._role_mappings.get(template_name, {}).values()),
            "output_schema": self._output_schemas.get(template_name),
            "example_count": len(self._examples.get(template_name, [])),
        }
    
    def validate_template(self, template_name: str) -> dict[str, Any]:
        """Validate template."""
        try:
            template = self._get_latest_template(template_name)
            variables = self._extract_variables(template)
            
            errors = []
            warnings = []
            
            if "{" in template and "}" not in template:
                errors.append("Unmatched opening brace")
            if "}" in template and "{" not in template:
                errors.append("Unmatched closing brace")
            
            for var in variables:
                if var not in self._defaults and var not in self._allowed_missing:
                    warnings.append(f"Variable '{var}' has no default value")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "variables_found": variables,
            }
        except KeyError as e:
            return {"valid": False, "errors": [f"Template not found: {e}"], "warnings": [], "variables_found": []}
    
    # Helper methods
    def _register_default_templates(self) -> None:
        """Register templates by reading all files from the templates folder."""
        load_default_templates(self)
    
    def _is_block_template(self, template: str) -> bool:
        """Check if template uses `{{ }}`, `{% %}` or `{# #}` syntax."""
        return bool(re.search(r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}", template, re.DOTALL))

    def _render_block_template(self, template: str, variables: dict[str, Any]) -> str:
        """Render a block template with the stdlib engine (undefined variables stay visible)."""
        variables_with_defaults = dict(variables)
        for var in self._allowed_missing:
            variables_with_defaults.setdefault(var, "")
        try:
            return render_template(template, variables_with_defaults, self._custom_filters)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template rendering failed: {e}") from e

    def _get_latest_template(self, name: str) -> str:
        """Get latest version of template."""
        matching = [k for k in self._templates.keys() if k.startswith(f"{name}:")]
        if not matching:
            raise KeyError(f"Template not found: {name}")
        return self._templates[sorted(matching)[-1]]
    
    def _extract_variables(self, template: str) -> list[str]:
        """Extract variables from template."""
        return list(set(re.findall(r'\{([^}]+)\}', template)))
    
    def _merge_variables(self, template_vars: list[str], provided_vars: dict[str, Any]) -> dict[str, Any]:
        """Merge variables."""
        merged = {}
        merged.update(self._defaults)
        merged.update(self._partial_vars)
        merged.update(provided_vars)
        return merged
    
    def _select_examples(self, template_name: str, variables: dict[str, Any]) -> list[dict[str, Any]]:
        """Select examples."""
        examples = self._examples.get(template_name, [])
        if not examples:
            return []
        
        config = self._example_selectors.get(template_name, {"type": "fixed", "max_examples": 3})
        max_examples = config.get("max_examples", 3)
        
        if config.get("type") == "random":
            import random
            return random.sample(examples, min(len(examples), max_examples))
        return examples[:max_examples]
    
    def _format_examples(self, template_name: str, examples: list[dict[str, Any]]) -> str:
        """Format examples."""
        if not examples:
            return ""
        
        template = self._example_templates.get(template_name, "Input: {input}\nOutput: {output}")
        formatted = []
        for ex in examples:
            try:
                formatted.append(template.format(**ex))
            except KeyError:
                continue
        return "\n\n".join(formatted) + "\n\n" if formatted else ""
    
    def _create_messages(self, template_name: str, content: str) -> list[SkyeMessage]:
        """Create proper SkyeMessage objects for completion API."""
        role_mapping = self._role_mappings.get(template_name, {})
        
        # Parse role sections if configured or if content has role markers
        if role_mapping or self._has_role_markers(content):
            sections = self._parse_role_sections(content)
            messages = []
            for role, section_content in sections:
                if section_content.strip():  # Only create messages with content
                    if role == "system":
                        messages.append(SystemMessage(content=section_content.strip()))
                    elif role == "assistant":
                        messages.append(AssistantMessage(content=section_content.strip()))
                    else:
                        messages.append(UserMessage(content=section_content.strip()))
            
            # Ensure we always return at least one message
            return messages if messages else [UserMessage(content=content)]
        
        # Default: single user message for completion API
        return [UserMessage(content=content)]
    
    def _has_role_markers(self, content: str) -> bool:
        """Check if content has role markers like [SYSTEM], [USER], [ASSISTANT]."""
        return bool(re.search(r'^\[(?:SYSTEM|USER|ASSISTANT)\]', content, re.MULTILINE))
    
    def _parse_role_sections(self, content: str) -> list[tuple[str, str]]:
        """Parse role sections from content with proper message boundaries."""
        sections = []
        current_role = "user"
        current_content = []
        
        for line in content.split('\n'):
            role_match = re.match(r'^\[(\w+)\]', line.strip())
            if role_match:
                # Save previous section if it has content
                if current_content:
                    sections.append((current_role, '\n'.join(current_content).strip()))
                    current_content = []
                # Update current role
                current_role = role_match.group(1).lower()
            else:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections.append((current_role, '\n'.join(current_content).strip()))
        
        return sections
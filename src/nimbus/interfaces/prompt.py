"""Prompt builder interface for template management.

This module defines the abstract interface for prompt template management
and rendering. It enables reusable, parameterized prompts with version control.

Inspired by:
- **Promptify's Prompter**: Jinja2 templates, variable validation, default values, few-shot examples
- **LangChain's BasePromptTemplate**: Partial variables, input/output parsers,
  invoke pattern, multimodal support

Comprehensive Features:
- **Jinja2 Template Engine**: Full Jinja2 support with filters, macros, and inheritance
- **Few-Shot Learning**: Dynamic example selection and formatting
- **Multimodal Support**: Text, images, audio, video content in prompts
- **Template Management**: Versioning, loading from files/strings, composition
- **Variable Handling**: Validation, defaults, partial binding, type checking
- **Message Formatting**: System, user, assistant message roles with metadata
- **Example Selectors**: Semantic similarity, random, fixed example selection
- **Output Parsing**: Structured output schemas and validation

Example:
    >>> from nimbus.interfaces.prompt import PromptBuilderInterface
    >>> from nimbus.messages import UserMessage
    >>>
    >>> class MyPromptBuilder(PromptBuilderInterface):
    ...     def render(self, template_name: str, variables: dict) -> list:
    ...         # Implementation here
    ...         pass
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from nimbus.messages import NimbusMessage


class PromptBuilderInterface(ABC):
    """Abstract interface for prompt template management.

    This interface defines the contract for managing and rendering prompt templates.
    Implementations should support Jinja2-style templates with variable injection,
    validation, and default values. Inspired by Promptify's Prompter design.

    Key Features:
    - Template rendering with variable substitution
    - Support for loading templates from files or strings
    - Variable validation with allowed missing variables
    - Default values for optional template variables
    - Few-shot example injection support
    - Template versioning

    Example:
        >>> class Jinja2PromptBuilder(PromptBuilderInterface):
        ...     def __init__(self):
        ...         self.templates = {}
        ...         self.allowed_missing = ["examples", "description", "output_format"]
        ...         self.defaults = {}
        ...
        ...     def render(self, template_name: str, variables: dict) -> list:
        ...         template = self.templates.get(template_name, "")
        ...         # Merge with defaults
        ...         merged_vars = {**self.defaults, **variables}
        ...         content = template.format(**merged_vars)
        ...         return [UserMessage(content=content)]
        ...
        ...     def register_template(self, name: str, template: str, version: str = "1.0") -> None:
        ...         self.templates[f"{name}:{version}"] = template
        ...
        ...     def get_template(self, name: str, version: str | None = None) -> str:
        ...         key = f"{name}:{version}" if version else f"{name}:1.0"
        ...         return self.templates.get(key, "")
        ...
        ...     def get_template_variables(self, template_name: str) -> list[str]:
        ...         # Extract variables from template
        ...         return []
        ...
        ...     def set_default_values(self, defaults: dict[str, Any]) -> None:
        ...         self.defaults.update(defaults)
        ...
        ...     def set_allowed_missing_variables(self, variables: list[str]) -> None:
        ...         self.allowed_missing.extend(variables)
    """

    @abstractmethod
    def render(self, template_name: str, variables: dict[str, Any]) -> list[NimbusMessage]:
        """Render a template with provided variables into messages.

        Similar to Promptify's generate() method, this renders a template by:
        1. Loading the template by name
        2. Merging provided variables with default values
        3. Validating required variables are present
        4. Rendering the template with variable substitution
        5. Converting the result to NimbusMessage objects

        Args:
            template_name: Name of the template to render.
            variables: Dictionary of variables to inject into the template.

        Returns:
            List of NimbusMessage objects created from the rendered template.

        Raises:
            KeyError: If the template name is not found.
            ValueError: If required variables are missing.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("ner", "Extract entities from: {text_input}")
            >>> builder.set_default_values({"domain": "general"})
            >>> messages = builder.render("ner", {"text_input": "Alice works at Google"})
            >>> messages[0].content
            'Extract entities from: Alice works at Google'
        """
        pass

    @abstractmethod
    def register_template(
        self, name: str, template: str, version: str = "1.0", from_string: bool = True
    ) -> None:
        """Register a new prompt template.

        Supports loading templates from strings or file paths, similar to
        Promptify's template loading mechanism.

        Args:
            name: Unique name for the template.
            template: The template string or file path (format depends on implementation).
            version: Version identifier for the template (default: "1.0").
            from_string: If True, treat template as string; if False, treat as file path.

        Raises:
            ValueError: If the template is invalid or name is already registered.
            FileNotFoundError: If from_string is False and file doesn't exist.

        Example:
            >>> builder = MyPromptBuilder()
            >>> # From string
            >>> builder.register_template(
            ...     "summarize",
            ...     "Summarize: {text}",
            ...     version="1.0",
            ...     from_string=True
            ... )
            >>> # From file
            >>> builder.register_template(
            ...     "ner",
            ...     "templates/ner.jinja",
            ...     version="1.0",
            ...     from_string=False
            ... )
        """
        pass

    @abstractmethod
    def get_template(self, name: str, version: str | None = None) -> str:
        """Retrieve a template by name and optional version.

        Args:
            name: Name of the template to retrieve.
            version: Optional version identifier. If None, returns the latest version.

        Returns:
            The template string.

        Raises:
            KeyError: If the template name or version is not found.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("greeting", "Hello {name}!", version="1.0")
            >>> template = builder.get_template("greeting", version="1.0")
            >>> template
            'Hello {name}!'
        """
        pass

    @abstractmethod
    def get_template_variables(self, template_name: str) -> list[str]:
        """Extract variable names from a template.

        Similar to Promptify's template variable extraction, this identifies
        all variables that need to be provided when rendering the template.

        Args:
            template_name: Name of the template to analyze.

        Returns:
            List of variable names found in the template.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("test", "Hello {name}, you are {age} years old")
            >>> builder.get_template_variables("test")
            ['name', 'age']
        """
        pass

    @abstractmethod
    def set_default_values(self, defaults: dict[str, Any]) -> None:
        """Set default values for template variables.

        Similar to Promptify's default_variable_values, these defaults are used
        when a variable is not provided in the render() call.

        Args:
            defaults: Dictionary mapping variable names to default values.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.set_default_values({
            ...     "temperature": 0.7,
            ...     "domain": "general",
            ...     "output_format": "json"
            ... })
        """
        pass

    @abstractmethod
    def set_allowed_missing_variables(self, variables: list[str]) -> None:
        """Set variables that are allowed to be missing from templates.

        Similar to Promptify's allowed_missing_variables, these variables
        won't trigger validation errors if not provided.

        Common allowed missing variables:
        - "examples": For few-shot examples
        - "description": For task descriptions
        - "output_format": For output format specifications

        Args:
            variables: List of variable names that can be omitted.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.set_allowed_missing_variables([
            ...     "examples",
            ...     "description",
            ...     "output_format"
            ... ])
        """
        pass

    @abstractmethod
    def partial(self, **kwargs: str | Callable[[], str]) -> "PromptBuilderInterface":
        """Return a new builder with partial variables bound.

        Inspired by LangChain's partial() method, this allows you to bind some
        variables ahead of time, creating a new template that expects fewer inputs.
        Variables can be either static strings or callables that return strings
        (useful for dynamic values like timestamps).

        Args:
            **kwargs: Variables to bind. Values can be strings or callables.

        Returns:
            A new PromptBuilderInterface with partial variables bound.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("greeting", "Hello {name}, today is {date}")
            >>> # Bind date dynamically
            >>> import datetime
            >>> partial_builder = builder.partial(date=lambda: datetime.date.today().isoformat())
            >>> # Now only need to provide name
            >>> messages = partial_builder.render("greeting", {"name": "Alice"})
        """
        pass

    @abstractmethod
    def invoke(self, template_name: str, variables: dict[str, Any]) -> list[NimbusMessage]:
        """Invoke the template rendering (LangChain-style API).

        This is an alias for render() that follows LangChain's invoke pattern,
        making it compatible with LangChain's Runnable interface.

        Args:
            template_name: Name of the template to render.
            variables: Dictionary of variables to inject.

        Returns:
            List of NimbusMessage objects.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("test", "Hello {name}")
            >>> messages = builder.invoke("test", {"name": "Bob"})
        """
        pass

    @abstractmethod
    def format(self, template_name: str, variables: dict[str, Any]) -> str:
        """Format template to a string (LangChain-style API).

        Similar to render() but returns a plain string instead of NimbusMessage objects.
        Useful when you need the raw prompt text.

        Args:
            template_name: Name of the template to format.
            variables: Dictionary of variables to inject.

        Returns:
            Formatted prompt as a string.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("test", "Hello {name}")
            >>> prompt_str = builder.format("test", {"name": "Charlie"})
            >>> prompt_str
            'Hello Charlie'
        """
        pass

    # ===== Few-Shot Learning Support =====

    @abstractmethod
    def add_examples(
        self,
        template_name: str,
        examples: list[dict[str, Any]],
        example_template: str | None = None,
    ) -> None:
        """Add few-shot examples to a template.

        Inspired by Promptify and LangChain's few-shot prompting, this allows
        adding examples that will be formatted and injected into the prompt.

        Args:
            template_name: Name of the template to add examples to.
            examples: List of example dictionaries with input/output pairs.
            example_template: Optional template for formatting each example.
                If None, uses a default format.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("ner", "Extract entities from: {text}")
            >>> builder.add_examples("ner", [
            ...     {"text": "Alice works at Google", "entities": ["Alice", "Google"]},
            ...     {"text": "Bob lives in NYC", "entities": ["Bob", "NYC"]}
            ... ])
        """
        pass

    @abstractmethod
    def set_example_selector(
        self, template_name: str, selector_type: str, max_examples: int = 5, **selector_kwargs: Any
    ) -> None:
        """Set an example selector for dynamic few-shot selection.

        Inspired by LangChain's ExampleSelector, this enables dynamic selection
        of the most relevant examples based on the input.

        Args:
            template_name: Name of the template.
            selector_type: Type of selector ("semantic", "random", "fixed", "length_based").
            max_examples: Maximum number of examples to select.
            **selector_kwargs: Additional arguments for the selector (e.g., vectorstore config).

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.set_example_selector(
            ...     "ner",
            ...     selector_type="semantic",
            ...     max_examples=3,
            ...     vectorstore="chroma"
            ... )
        """
        pass

    # ===== Multimodal Support =====

    @abstractmethod
    def add_image_content(
        self, template_name: str, image_variable: str, image_format: str = "url"
    ) -> None:
        """Configure template to support image content.

        Enables multimodal prompts with images, following LangChain's
        multimodal prompt patterns.

        Args:
            template_name: Name of the template.
            image_variable: Variable name that will contain image data.
            image_format: Format of image data ("url", "base64", "path").

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("vision", "Describe this image: {image}")
            >>> builder.add_image_content("vision", "image", image_format="url")
            >>> messages = builder.render("vision", {
            ...     "image": "https://example.com/image.jpg"
            ... })
        """
        pass

    @abstractmethod
    def add_multimodal_content(self, template_name: str, content_variables: dict[str, str]) -> None:
        """Configure template for multiple content types.

        Supports text, images, audio, video, and other modalities.

        Args:
            template_name: Name of the template.
            content_variables: Mapping of variable names to content types.
                Types: "text", "image", "audio", "video", "file"

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.add_multimodal_content("analyze", {
            ...     "image": "image",
            ...     "audio": "audio",
            ...     "text": "text"
            ... })
        """
        pass

    # ===== Jinja2 Advanced Features =====

    @abstractmethod
    def register_jinja_filter(self, filter_name: str, filter_func: Callable[[Any], Any]) -> None:
        """Register a custom Jinja2 filter.

        Allows extending Jinja2 templates with custom filters for
        text processing, formatting, etc.

        Args:
            filter_name: Name of the filter to use in templates.
            filter_func: Function that implements the filter.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_jinja_filter("uppercase", lambda x: x.upper())
            >>> # In template: "{{ name | uppercase }}"
        """
        pass

    @abstractmethod
    def register_jinja_macro(self, macro_name: str, macro_template: str) -> None:
        """Register a Jinja2 macro for reusable template components.

        Args:
            macro_name: Name of the macro.
            macro_template: Jinja2 macro definition.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_jinja_macro(
            ...     "format_entity",
            ...     "{% macro format_entity(name, type) %}{{ name }} ({{ type }}){% endmacro %}"
            ... )
        """
        pass

    @abstractmethod
    def compose_templates(
        self, name: str, template_parts: list[str], separator: str = "\n\n"
    ) -> None:
        """Compose a new template from multiple template parts.

        Inspired by LangChain's PipelinePromptTemplate, this enables
        building complex prompts from reusable components.

        Args:
            name: Name for the composed template.
            template_parts: List of template names to compose.
            separator: String to join template parts.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.register_template("system", "You are a helpful assistant")
            >>> builder.register_template("task", "Extract entities from: {text}")
            >>> builder.compose_templates("full_prompt", ["system", "task"])
        """
        pass

    # ===== Message Role Management =====

    @abstractmethod
    def set_message_roles(self, template_name: str, role_mapping: dict[str, str]) -> None:
        """Set message roles for different template sections.

        Enables creating chat-style prompts with system, user, and assistant roles.

        Args:
            template_name: Name of the template.
            role_mapping: Mapping of template sections to roles.
                Roles: "system", "user", "assistant", "capability"

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.set_message_roles("chat", {
            ...     "system_prompt": "system",
            ...     "user_input": "user",
            ...     "examples": "assistant"
            ... })
        """
        pass

    @abstractmethod
    def add_message_placeholder(
        self, template_name: str, placeholder_name: str, role: str = "user"
    ) -> None:
        """Add a placeholder for dynamic message insertion.

        Inspired by LangChain's MessagesPlaceholder, this allows inserting
        conversation history or dynamic messages.

        Args:
            template_name: Name of the template.
            placeholder_name: Variable name for the placeholder.
            role: Default role for messages in the placeholder.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.add_message_placeholder("chat", "history", role="user")
            >>> # Later: render with history=[msg1, msg2, ...]
        """
        pass

    # ===== Output Schema & Validation =====

    @abstractmethod
    def set_output_schema(self, template_name: str, schema: dict[str, Any] | type) -> None:
        """Set expected output schema for structured outputs.

        Enables validation and parsing of LLM responses into structured formats.

        Args:
            template_name: Name of the template.
            schema: JSON schema dict or Pydantic model class.

        Example:
            >>> from pydantic import BaseModel
            >>> class Entity(BaseModel):
            ...     name: str
            ...     type: str
            >>> builder = MyPromptBuilder()
            >>> builder.set_output_schema("ner", Entity)
        """
        pass

    @abstractmethod
    def get_output_instructions(self, template_name: str) -> str:
        """Get formatted output instructions based on schema.

        Generates instructions for the LLM on how to format its output
        based on the configured output schema.

        Args:
            template_name: Name of the template.

        Returns:
            Formatted output instructions string.

        Example:
            >>> builder = MyPromptBuilder()
            >>> builder.set_output_schema("ner", {"entities": ["name", "type"]})
            >>> instructions = builder.get_output_instructions("ner")
        """
        pass

    # ===== Template Metadata & Introspection =====

    @abstractmethod
    def get_template_metadata(self, template_name: str) -> dict[str, Any]:
        """Get metadata about a template.

        Returns information about the template including variables, examples,
        content types, roles, and other configuration.

        Args:
            template_name: Name of the template.

        Returns:
            Dictionary with template metadata:
                - "variables": List of required variables
                - "optional_variables": List of optional variables
                - "has_examples": Whether examples are configured
                - "content_types": List of content types (text, image, etc.)
                - "message_roles": Configured message roles
                - "output_schema": Output schema if configured

        Example:
            >>> builder = MyPromptBuilder()
            >>> metadata = builder.get_template_metadata("ner")
            >>> print(f"Required variables: {metadata['variables']}")
        """
        pass

    @abstractmethod
    def validate_template(self, template_name: str) -> dict[str, Any]:
        """Validate a template for correctness.

        Checks for syntax errors, undefined variables, and other issues.

        Args:
            template_name: Name of the template to validate.

        Returns:
            Dictionary with validation results:
                - "valid": Boolean indicating if template is valid
                - "errors": List of error messages
                - "warnings": List of warning messages

        Example:
            >>> builder = MyPromptBuilder()
            >>> result = builder.validate_template("ner")
            >>> if not result["valid"]:
            ...     print(f"Errors: {result['errors']}")
        """
        pass

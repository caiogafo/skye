"""Unit tests for BasePromptBuilder."""

# Import test data from the proper location
import sys
from pathlib import Path

import pytest

from skye.base.messages import UserMessage
from skye.prompts import BasePromptBuilder

test_data_path = Path(__file__).parent / "test_data"
sys.path.insert(0, str(test_data_path.parent))

try:
    from test_data import load_classification_examples, load_ner_examples
except ImportError:
    # Fallback if import fails
    def load_ner_examples():
        return [{"text": "Apple Inc.", "entities": [{"text": "Apple Inc.", "label": "ORG"}]}]
    
    def load_classification_examples():
        return [{"text": "Great!", "category": "positive"}]


class TestBasePromptBuilder:
    """Test cases for BasePromptBuilder."""
    
    def test_initialization(self):
        """Test builder initializes with templates loaded from files."""
        builder = BasePromptBuilder()
        
        # Should have templates loaded from the templates folder
        template_names = [key.split(':')[0] for key in builder._templates.keys()]
        
        # Check that some templates are loaded (the exact names depend on what's in templates folder)
        assert len(template_names) > 0
        
        # Check that common templates exist (these should be in the templates folder)
        expected_templates = ["ner", "classification", "chat", "question_answering"]
        found_templates = [name for name in expected_templates if any(name in key for key in builder._templates.keys())]
        assert len(found_templates) > 0, f"Expected some of {expected_templates}, found templates: {template_names}"
    
    def test_register_and_get_template(self):
        """Test template registration and retrieval."""
        builder = BasePromptBuilder()
        
        # Register template
        builder.register_template("test", "Hello {name}!")
        
        # Get template
        template = builder.get_template("test")
        assert template == "Hello {name}!"
        
        # Get with version
        template = builder.get_template("test", "1.0")
        assert template == "Hello {name}!"
    
    def test_template_versioning(self):
        """Test template versioning."""
        builder = BasePromptBuilder()
        
        # Register multiple versions
        builder.register_template("test", "Version 1", "1.0")
        builder.register_template("test", "Version 2", "2.0")
        
        # Get specific versions
        assert builder.get_template("test", "1.0") == "Version 1"
        assert builder.get_template("test", "2.0") == "Version 2"
        
        # Get latest (should be 2.0)
        assert builder.get_template("test") == "Version 2"
    
    def test_render_basic(self):
        """Test basic template rendering."""
        builder = BasePromptBuilder()
        
        builder.register_template("greeting", "Hello {name}!")
        messages = builder.render("greeting", {"name": "Alice"})
        
        assert len(messages) == 1
        assert isinstance(messages[0], UserMessage)
        assert messages[0].content == "Hello Alice!"
    
    def test_render_with_defaults(self):
        """Test rendering with default values."""
        builder = BasePromptBuilder()
        
        builder.register_template("greeting", "Hello {name} from {location}!")
        builder.set_default_values({"location": "Earth"})
        
        messages = builder.render("greeting", {"name": "Bob"})
        assert messages[0].content == "Hello Bob from Earth!"
        
        # Override default
        messages = builder.render("greeting", {"name": "Bob", "location": "Mars"})
        assert messages[0].content == "Hello Bob from Mars!"
    
    def test_render_with_missing_allowed_variables(self):
        """Test rendering with allowed missing variables."""
        builder = BasePromptBuilder()
        
        builder.register_template("optional", "Hello {name}! {optional_msg}")
        builder.set_allowed_missing_variables(["optional_msg"])
        
        # Should not raise error for missing optional variable
        messages = builder.render("optional", {"name": "Charlie"})
        assert "Hello Charlie!" in messages[0].content
    
    def test_render_missing_required_variable(self):
        """Test error when required variable is missing."""
        builder = BasePromptBuilder()
        
        builder.register_template("required", "Hello {name}!")
        
        with pytest.raises(ValueError, match="Missing required variable: name"):
            builder.render("required", {})
    
    def test_get_template_variables(self):
        """Test variable extraction."""
        builder = BasePromptBuilder()
        
        builder.register_template("multi_var", "Hello {name} from {location} at {time}!")
        variables = builder.get_template_variables("multi_var")
        
        assert set(variables) == {"name", "location", "time"}
    
    def test_partial_binding(self):
        """Test partial variable binding."""
        builder = BasePromptBuilder()
        
        builder.register_template("partial_test", "Hello {name} from {location}!")
        
        # Create partial with location bound
        partial_builder = builder.partial(location="Mars")
        
        # Should only need name now
        messages = partial_builder.render("partial_test", {"name": "Dave"})
        assert messages[0].content == "Hello Dave from Mars!"
    
    def test_partial_with_callable(self):
        """Test partial binding with callable."""
        builder = BasePromptBuilder()
        
        builder.register_template("time_test", "Current time: {timestamp}")
        
        # Bind with callable
        partial_builder = builder.partial(timestamp=lambda: "2024-01-01")
        
        messages = partial_builder.render("time_test", {})
        assert messages[0].content == "Current time: 2024-01-01"
    
    def test_langchain_style_apis(self):
        """Test LangChain-style invoke and format methods."""
        builder = BasePromptBuilder()
        
        builder.register_template("test", "Hello {name}!")
        
        # Test invoke
        messages = builder.invoke("test", {"name": "Eve"})
        assert len(messages) == 1
        assert messages[0].content == "Hello Eve!"
        
        # Test format
        formatted = builder.format("test", {"name": "Eve"})
        assert formatted == "Hello Eve!"
    
    def test_add_examples(self):
        """Test adding few-shot examples."""
        builder = BasePromptBuilder()
        
        # Register a simple template for testing
        builder.register_template("simple_classification", "Classify: {text}\nCategories: {categories}\n\n{examples}Category:")
        
        examples = [
            {"input": "apple", "output": "fruit"},
            {"input": "carrot", "output": "vegetable"}
        ]
        
        builder.add_examples("simple_classification", examples)
        
        # Render should include examples
        messages = builder.render("simple_classification", {
            "text": "banana",
            "categories": "fruit, vegetable"
        })
        
        content = messages[0].content
        assert "apple" in content
        assert "fruit" in content
        assert "carrot" in content
        assert "vegetable" in content
    
    def test_custom_example_template(self):
        """Test custom example formatting."""
        builder = BasePromptBuilder()
        
        examples = [{"word": "hello", "translation": "hola"}]
        builder.add_examples("translate", examples, "English: {word} → Spanish: {translation}")
        
        # Register a simple template that uses examples
        builder.register_template("translate", "Translate: {text}\n\n{examples}Translation:")
        
        messages = builder.render("translate", {"text": "goodbye"})
        content = messages[0].content
        assert "English: hello → Spanish: hola" in content
    
    def test_multimodal_content(self):
        """Test multimodal content configuration."""
        builder = BasePromptBuilder()
        
        builder.register_template("image_analysis", "Analyze: {image}")
        builder.add_image_content("image_analysis", "image", "url")
        
        messages = builder.render("image_analysis", {"image": "https://example.com/image.jpg"})
        assert "https://example.com/image.jpg" in messages[0].content
        
        # Check metadata
        metadata = builder.get_template_metadata("image_analysis")
        assert "image:url" in metadata["content_types"]
    
    def test_template_composition(self):
        """Test template composition."""
        builder = BasePromptBuilder()
        
        builder.register_template("part1", "First part")
        builder.register_template("part2", "Second part")
        
        builder.compose_templates("combined", ["part1", "part2"])
        
        template = builder.get_template("combined")
        assert "First part" in template
        assert "Second part" in template
    
    def test_output_schema(self):
        """Test output schema configuration."""
        builder = BasePromptBuilder()
        
        schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        builder.set_output_schema("test", schema)
        
        instructions = builder.get_output_instructions("test")
        assert "JSON" in instructions
        assert str(schema) in instructions
    
    def test_template_metadata(self):
        """Test template metadata retrieval."""
        builder = BasePromptBuilder()
        
        builder.register_template("meta_test", "Hello {name}! {optional}")
        builder.set_allowed_missing_variables(["optional"])
        builder.add_examples("meta_test", [{"name": "test", "greeting": "hi"}])
        
        metadata = builder.get_template_metadata("meta_test")
        
        assert "name" in metadata["variables"]
        assert "optional" in metadata["optional_variables"]
        assert metadata["has_examples"] is True
        assert metadata["example_count"] == 1
    
    def test_template_validation(self):
        """Test template validation."""
        builder = BasePromptBuilder()
        
        # Valid template
        builder.register_template("valid", "Hello {name}!")
        result = builder.validate_template("valid")
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Template with warnings
        assert len(result["warnings"]) > 0  # name has no default
        
        # Invalid template (unmatched braces)
        builder.register_template("invalid", "Hello {name!")
        result = builder.validate_template("invalid")
        assert result["valid"] is False
        assert "Unmatched opening brace" in result["errors"]
    
    def test_default_templates_work(self):
        """Test that loaded templates can be rendered."""
        builder = BasePromptBuilder()
        
        # Get available templates
        available_templates = list(builder._templates.keys())
        assert len(available_templates) > 0, "No templates loaded"
        
        # Test memory agent template
        builder.register_template("memory_agent_test", "You are an AI with memory.\n\n{% if episodic_memory %}## Past conversations:\n{% for memory in episodic_memory %}{{ memory.content }}{% endfor %}{% endif %}\n\nUser: {{ input }}")
        messages = builder.render("memory_agent_test", {
            "input": "Hello, do you remember me?",
            "episodic_memory": [{"content": "User said hello yesterday"}]
        })
        assert len(messages) == 1
        assert "remember me" in messages[0].content
        assert "hello yesterday" in messages[0].content
        
        # Test tool agent template
        builder.register_template("tool_agent_test", "You can use tools.\n\nAvailable tools:\n{% for tool in tools %}- {{ tool.name }}: {{ tool.description }}\n{% endfor %}\n\nUser: {{ input }}")
        messages = builder.render("tool_agent_test", {
            "input": "What tools do you have?",
            "tools": [{"name": "calculator", "description": "Performs calculations"}]
        })
        assert "calculator" in messages[0].content
        assert "calculations" in messages[0].content
        
        # Test enhanced NER template
        builder.register_template("enhanced_ner", "Extract entities from: {{ text }}\n\n{% if domain %}Domain: {{ domain }}{% endif %}\n\n{% if labels %}Entity types: {% for label in labels %}{{ label.name }}{% endfor %}{% endif %}")
        messages = builder.render("enhanced_ner", {
            "text": "Apple Inc. was founded by Steve Jobs.",
            "domain": "business",
            "labels": [{"name": "ORG"}, {"name": "PERSON"}]
        })
        assert "Apple Inc." in messages[0].content
        assert "business" in messages[0].content
        assert "ORG" in messages[0].content
        
        # Test code agent template
        builder.register_template("code_agent_test", "You are a code assistant.\n\n{% if programming_language %}Language: {{ programming_language }}{% endif %}\n\n{% if task_type %}Task: {{ task_type }}{% endif %}\n\n[USER]\n{{ input }}")
        messages = builder.render("code_agent_test", {
            "input": "Write a function to sort a list",
            "programming_language": "Python",
            "task_type": "code_generation"
        })
        assert "Python" in messages[0].content
        assert "code_generation" in messages[0].content
        
        # Test multimodal agent template
        builder.register_template("multimodal_test", "Analyze content.\n\n{% if images %}Images: {% for img in images %}{{ img.description }}{% endfor %}{% endif %}\n\n[USER]\n{{ input }}")
        messages = builder.render("multimodal_test", {
            "input": "What do you see?",
            "images": [{"description": "A photo of a cat"}]
        })
        assert "photo of a cat" in messages[0].content
    
    def test_role_based_messages(self):
        """Test role-based message creation."""
        builder = BasePromptBuilder()
        
        # Register template with role markers
        builder.register_template("chat_roles", "[SYSTEM]\nYou are helpful.\n\n[USER]\nHello!")
        builder.set_message_roles("chat_roles", {"system": "system", "user": "user"})
        
        messages = builder.render("chat_roles", {})
        
        # Should create multiple messages based on roles
        assert len(messages) >= 1
        # Content should be parsed correctly
        content = messages[0].content
        assert "helpful" in content or "Hello" in content
    
    def test_file_template_loading(self):
        """Test loading templates from files."""
        builder = BasePromptBuilder()
        
        # Create a temporary template file
        import os
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("File template: {content}")
            temp_file = f.name
        
        try:
            # Load from file
            builder.register_template("file_test", temp_file, from_string=False)
            
            messages = builder.render("file_test", {"content": "loaded from file"})
            assert "loaded from file" in messages[0].content
        finally:
            os.unlink(temp_file)
    
    def test_nonexistent_template_error(self):
        """Test error when template doesn't exist."""
        builder = BasePromptBuilder()
        
        with pytest.raises(KeyError, match="Template not found"):
            builder.render("nonexistent", {})
    
    def test_example_selectors(self):
        """Test different example selection strategies."""
        builder = BasePromptBuilder()
        
        examples = [{"input": f"example{i}", "output": f"result{i}"} for i in range(10)]
        builder.add_examples("selector_test", examples)
        
        # Test fixed selector (default)
        builder.set_example_selector("selector_test", "fixed", max_examples=3)
        selected = builder._select_examples("selector_test", {})
        assert len(selected) == 3
        assert selected[0]["input"] == "example0"
        
        # Test random selector
        builder.set_example_selector("selector_test", "random", max_examples=3)
        selected = builder._select_examples("selector_test", {})
        assert len(selected) == 3
    def test_agent_templates(self):
        """Test agent-specific templates."""
        builder = BasePromptBuilder()
        
        # Test memory agent template structure
        builder.register_template("memory_agent", """[SYSTEM]
You are an AI with memory capabilities.

{% if episodic_memory %}
## Past conversations:
{% for memory in episodic_memory %}
- {{ memory.content }}{% if memory.timestamp %} ({{ memory.timestamp }}){% endif %}
{% endfor %}
{% endif %}

[USER]
{{ input }}""")
        
        messages = builder.render("memory_agent", {
            "input": "What did we discuss before?",
            "episodic_memory": [
                {"content": "User asked about weather", "timestamp": "2 hours ago"},
                {"content": "User mentioned vacation plans", "timestamp": "1 day ago"}
            ]
        })
        
        content = messages[0].content
        assert "Past conversations:" in content
        assert "weather" in content
        assert "vacation plans" in content
        assert "2 hours ago" in content
        
        # Test tool agent template structure
        builder.register_template("tool_agent", """
You can use these tools:
{% for tool in tools -%}
- "{{ tool.name }}": {{ tool.description }}
{% endfor %}

Respond with JSON: {"action": "tool_name", "action_input": "input"}

[USER]
{{ input }}
""")
        
        messages = builder.render("tool_agent", {
            "input": "Calculate 2 + 2",
            "tools": [
                {"name": "calculator", "description": "Performs mathematical calculations"},
                {"name": "search", "description": "Searches for information"}
            ]
        })
        
        content = messages[0].content
        assert "calculator" in content
        assert "mathematical calculations" in content
        assert "search" in content
        assert "JSON" in content
    
    def test_enhanced_ner_template(self):
        """Test enhanced NER template with domain and labels."""
        builder = BasePromptBuilder()
        
        builder.register_template("enhanced_ner", """
{% if domain %}
Domain: {{ domain }}
{% endif %}

Entity types:
{% for label in labels %}
- {{ label.name }}: {{ label.description }}
{% endfor %}

Text: {{ text }}

Extract entities in JSON format.
""")
        
        messages = builder.render("enhanced_ner", {
            "text": "Dr. Smith works at Google in California.",
            "domain": "business",
            "labels": [
                {"name": "PERSON", "description": "Names of people"},
                {"name": "ORG", "description": "Organizations"},
                {"name": "LOC", "description": "Locations"}
            ]
        })
        
        content = messages[0].content
        assert "Domain: business" in content
        assert "PERSON: Names of people" in content
        assert "ORG: Organizations" in content
        assert "Dr. Smith works at Google" in content
    
    def test_multimodal_template(self):
        """Test multimodal template with different content types."""
        builder = BasePromptBuilder()
        
        # Allow missing optional fields
        builder.set_allowed_missing_variables(["image.url"])
        
        builder.register_template("multimodal", """
{% if task_type %}
Task: {{ task_type }}
{% endif %}

{% if images %}
Images provided:
{% for image in images %}
- {{ image.description }}{% if image.url %} ({{ image.url }}){% endif %}
{% endfor %}
{% endif %}

{% if documents %}
Documents:
{% for doc in documents %}
- {{ doc.title }}: {{ doc.content }}
{% endfor %}
{% endif %}

User: {{ input }}
""")
        
        messages = builder.render("multimodal", {
            "input": "Analyze the provided content",
            "task_type": "image_analysis",
            "images": [
                {"description": "Photo of a sunset", "url": "http://example.com/sunset.jpg"},
                {"description": "Chart showing sales data"}
            ],
            "documents": [
                {"title": "Report", "content": "Sales increased by 20%"}
            ]
        })
        
        content = messages[0].content
        assert "Task: image_analysis" in content
        assert "Photo of a sunset" in content
        assert "Chart showing sales data" in content
        assert "Report: Sales increased by 20%" in content
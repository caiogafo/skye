"""Message role management examples for Skye Prompts Support.

This script demonstrates message role management and template composition.
"""

from skye.prompts import MockPromptBuilder


def basic_message_roles():
    """Demonstrate basic message role assignment."""
    print("=== Basic Message Roles ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        name="chat_template",
        template="You are a helpful AI assistant. User: {user_message}"
    )
    
    builder.set_message_roles("chat_template", {
        "system_prompt": "system",
        "user_input": "user"
    })
    
    messages = builder.render("chat_template", {
        "user_message": "How do I clean messy data?"
    })
    
    print(f"Chat template: {messages[0].content}")
    print()


def template_composition():
    """Demonstrate template composition."""
    print("=== Template Composition ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template("system", "You are a helpful assistant.")
    builder.register_template("task", "Task: {task}")
    builder.register_template("format", "Format: {format}")
    
    builder.compose_templates("full_prompt", ["system", "task", "format"])
    
    messages = builder.render("full_prompt", {
        "task": "Extract entities",
        "format": "JSON"
    })
    
    print(f"Composed template: {messages[0].content}")
    print()


def main():
    """Run all message role examples."""
    print("Skye Prompts Support - Message Role Examples")
    print("=" * 50)
    
    basic_message_roles()
    template_composition()
    
    print("All message role examples completed!")


if __name__ == "__main__":
    main()
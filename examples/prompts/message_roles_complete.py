"""Message role management examples for Nimbus Prompts Support."""

from nimbus.prompts import MockPromptBuilder


def basic_message_roles():
    """Demonstrate basic message role assignment."""
    print("=== Basic Message Roles ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        name="chat_template",
        template="You are a helpful AI assistant specialized in {domain}.\n\nUser: {user_message}\n\nPlease provide a helpful response."
    )
    
    messages = builder.render("chat_template", {
        "domain": "data science",
        "user_message": "How do I clean messy data?"
    })
    
    print(f"Chat template rendered successfully!")
    print(f"Content: {messages[0].content}")
    print()


def main():
    """Run all message role examples."""
    print("Nimbus Prompts Support - Message Roles Complete")
    print("=" * 50)
    print()
    
    basic_message_roles()
    
    print("Message roles examples completed!")


if __name__ == "__main__":
    main()